import os
import aiohttp
import asyncio
from datetime import datetime
import socket
from urllib.parse import urlsplit


class LinkScannerClient:

    def __init__(
        self,
        session: aiohttp.ClientSession,
        timeout_sec: float = 10.0
    ):
        self.session = session
        self.timeout = aiohttp.ClientTimeout(
            total=timeout_sec
        )


    # Async functions

    # Finds the full url from any potential changed or shortend URLs
    async def expand_url(self, report_data: dict):

        try:

            async with self.session.get(
                    report_data["original_url"],
                    timeout=self.timeout
            ) as response:

                report_data["final_url"] = str(response.url)
                report_data["status_code"] = response.status

                report_data["redirect_history"] = [
                    str(redirect.url)
                    for redirect in response.history
                ]
                if report_data["redirect_history"]:
                    report_data["redirect_history"].append(
                        report_data["final_url"]
                    )

                report_data["uses_https"] = (
                    str(response.url).startswith("https://")
                )

        except Exception:

            report_data["final_url"] = "Could not resolve."
            report_data["status_code"] = None

            report_data["risk_score"] = "INVALID URL"

            report_data["risk_reason"] = (
                "The URL could not be reached."
            )

    async def check_virus_total(self, report_data: dict):

        headers = {
            "accept": "application/json",
            "x-apikey": os.getenv("VIRUSTOTAL_API_KEY"),
            "content-type": "application/x-www-form-urlencoded"
        }

        data = {
            "url": report_data["final_url"]
        }

        # Submit the URL to VirusTotal.
        async with self.session.post(
                "https://www.virustotal.com/api/v3/urls",
                headers=headers,
                data=data,
                timeout=self.timeout
        ) as response:

            submission = await response.json()

        analysis_id = submission["data"]["id"]

        # Poll VirusTotal until the analysis is complete.
        max_attempts = 10
        attempts = 0

        while attempts < max_attempts:

            async with self.session.get(
                    f"https://www.virustotal.com/api/v3/analyses/{analysis_id}",
                    headers=headers,
                    timeout=self.timeout
            ) as response:

                analysis = await response.json()

            attributes = analysis["data"]["attributes"]

            # Analysis is complete.
            if attributes["status"] == "completed":
                break

            attempts += 1

            await asyncio.sleep(1)

        # VirusTotal timed out.
        if attempts == max_attempts:
            report_data["virus_total"]["flagged_vendors"].append(
                "VirusTotal scan timed out."
            )

            return

        # Pull the statistics from the completed analysis.
        stats = attributes["stats"]
        results = attributes["results"]

        # Build a list of vendors that flagged the URL.
        flagged_vendors = []

        for vendor, vendor_data in results.items():

            category = vendor_data["category"]

            if category in ("malicious", "suspicious"):
                flagged_vendors.append(vendor)

        # Populate the report data.
        report_data["virus_total"]["malicious"] = (
            stats["malicious"]
        )

        report_data["virus_total"]["suspicious"] = (
            stats["suspicious"]
        )

        report_data["virus_total"]["harmless"] = (
            stats["harmless"]
        )

        report_data["virus_total"]["undetected"] = (
            stats["undetected"]
        )

        report_data["virus_total"]["flagged_vendors"] = (
            flagged_vendors
        )

    async def check_google_safe_browsing(self, report_data: dict):

        url = (
            "https://safebrowsing.googleapis.com/v5/"
            f"hashes:search?key={os.getenv('GOOGLESAFEBROWSING_API_KEY')}"
        )

        headers = {
            "Content-Type": "application/json"
        }

        payload = {

            "threatTypes": [
                "MALWARE",
                "SOCIAL_ENGINEERING",
                "UNWANTED_SOFTWARE",
                "POTENTIALLY_HARMFUL_APPLICATION"
            ],

            "uri": report_data["final_url"]

        }

        try:

            async with self.session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
            ) as response:

                results = await response.json()

        except Exception:

            report_data["safe_browsing"]["api_success"] = False
            return

        # API worked successfully.
        report_data["safe_browsing"]["api_success"] = True

        # No threats found.
        if "threats" not in results:
            report_data["safe_browsing"]["safe"] = True
            return

        # Threats were found.
        report_data["safe_browsing"]["safe"] = False

        threats = []

        for threat in results["threats"]:

            threat_type = threat["threatType"]

            if threat_type not in threats:
                threats.append(threat_type)

        report_data["safe_browsing"]["threats"] = threats

    # Regular helper functions
    # Turns the URL given into a universal URL. http:// or https://

    def get_domain_and_ip(self, report_data: dict):

        parsed_url = urlsplit(report_data["final_url"])

        domain = parsed_url.hostname

        if not domain:
            report_data["domain"] = "Unknown"
            report_data["ip_address"] = "Unknown"
            return

        try:
            ip_address = socket.gethostbyname(domain)

            report_data["domain"] = domain
            report_data["ip_address"] = ip_address

        except socket.gaierror:

            report_data["domain"] = domain
            report_data["ip_address"] = "Could not resolve."

    def normalize_url(self, url):

        url = url.strip()

        parsed_url = urlsplit(url)

        if not parsed_url.scheme:
            url = f"https://{url}"

        return url

    def get_status_code_description(self, status_code):

        descriptions = {

            200: "The website successfully returned the requested page.",

            301: "The URL permanently redirects to another location.",

            302: "The URL temporarily redirects to another location.",

            400: "The request sent to the server was invalid.",

            401: "Authentication is required to access this resource.",

            403: "Access to this resource is forbidden.",

            404: "The requested page or resource could not be found.",

            429: "Too many requests have been sent to the server.",

            500: "The server encountered an internal error.",

            502: "The server received an invalid response from an upstream server.",

            503: "The service is currently unavailable."

        }

        return descriptions.get(
            status_code,
            "No description available for this status code."
        )

    def calculate_risk_score(self, report_data):

        vt = report_data["virus_total"]
        gsb = report_data["safe_browsing"]

        if not gsb["safe"]:

            threats = gsb["threats"]

            if "MALWARE" in threats:

                report_data["risk_score"] = "CRITICAL"

                report_data["risk_reason"] = (
                    "Google Safe Browsing classified "
                    "this URL as malware."
                )

            elif "SOCIAL_ENGINEERING" in threats:

                report_data["risk_score"] = "HIGH"

                report_data["risk_reason"] = (
                    "Google Safe Browsing identified "
                    "this URL as phishing or social engineering."
                )

            else:

                report_data["risk_score"] = "HIGH"

                report_data["risk_reason"] = (
                    "Google Safe Browsing flagged this URL."
                )

            return

        if vt["malicious"] >= 5:

            report_data["risk_score"] = "HIGH"

            report_data["risk_reason"] = (
                f"{vt['malicious']} VirusTotal vendors "
                "classified this URL as malicious."
            )

        elif vt["malicious"] > 0:

            report_data["risk_score"] = "MEDIUM"

            report_data["risk_reason"] = (
                "VirusTotal reported malicious detections."
            )

        elif vt["suspicious"] > 0:

            report_data["risk_score"] = "LOW"

            report_data["risk_reason"] = (
                "VirusTotal reported suspicious detections."
            )

        else:

            report_data["risk_score"] = "SAFE"

            report_data["risk_reason"] = (
                "No security services reported any threats."
            )

    def generate_report(self, report_data):

        vt = report_data["virus_total"]
        gsb = report_data["safe_browsing"]

        report = f"""
    =========================================================
                    FRIEND LINK SCAN REPORT
    =========================================================

    Scan Information
    ---------------------------------------------------------

    Scan Date:
    {report_data["scan_date"]}

    Scanned By:
    {report_data["scanner_name"]}

    Discord ID:
    {report_data["scanner_id"]}


    General Information
    ---------------------------------------------------------

    Original URL:
    {report_data["original_url"]}

    Final URL:
    {report_data["final_url"]}

    Domain:
    {report_data["domain"]}

    IP Address:
    {report_data["ip_address"]}

    HTTPS Enabled:
    {"Yes" if report_data["uses_https"] else "No"}

    HTTP Status Code:
    {report_data["status_code"]}

    Meaning:
    {self.get_status_code_description(report_data["status_code"])}
    """

        report += f"""

    Redirect Information
    ---------------------------------------------------------

    Number of Redirects:
    {len(report_data["redirect_history"])}

    Redirect History:
    """

        if report_data["redirect_history"]:

            for url in report_data["redirect_history"]:
                report += f"\n- {url}"

        else:

            report += "\nNone"

        report += f"""



    VirusTotal Results
    ---------------------------------------------------------

    Malicious Detections:
    {vt["malicious"]}

    Suspicious Detections:
    {vt["suspicious"]}

    Harmless Detections:
    {vt["harmless"]}

    Undetected:
    {vt["undetected"]}


    Flagged Vendors:
    """

        if vt["flagged_vendors"]:

            for vendor in vt["flagged_vendors"]:
                report += f"\n- {vendor}"

        else:

            report += "\nNone"

        report += f"""



    Google Safe Browsing
    ---------------------------------------------------------

    API Status:
    {"Successful" if gsb["api_success"] else "Failed"}

    URL Status:
    {"SAFE" if gsb["safe"] else "UNSAFE"}

    Threats Found:
    """

        if gsb["threats"]:

            for threat in gsb["threats"]:
                report += f"\n- {threat}"

        else:

            report += "\nNone"

        report += f"""



    Risk Assessment
    ---------------------------------------------------------

    Risk Score:
    {report_data["risk_score"]}

    Reason:
    {report_data["risk_reason"]}



    Summary
    ---------------------------------------------------------
    """

        if report_data["risk_score"] == "SAFE":

            report += (
                "\nThis URL appears to be safe to visit at the time of this scan. "
                "No threats were reported by Google Safe "
                "Browsing or VirusTotal."
            )

        elif report_data["risk_score"] == "LOW":

            report += (
                "\nThis URL has minor suspicious indicators. "
                "Exercise caution before visiting."
            )

        elif report_data["risk_score"] == "MEDIUM":

            report += (
                "\nThis URL was flagged by one or more "
                "security vendors. Additional caution is "
                "recommended."
            )

        elif report_data["risk_score"] == "HIGH":

            report += (
                "\nThis URL presents a significant security "
                "risk and should not be trusted without "
                "further investigation."
            )

        elif report_data["risk_score"] == "CRITICAL":

            report += (
                "\nThis URL has been identified as malicious "
                "or phishing by one or more security services "
                "at the time of this scan and should be avoided."
            )

        else:

            report += (
                "\nThis URL could not be scanned successfully. "
                "The provided URL may be invalid or "
                "unreachable."
            )

        report += """



    =========================================================
                        END OF REPORT
    =========================================================
    """

        return report

    def save_report(self, report_data):

        domain = report_data["domain"]

        directory = f"./link_reports/{domain}"

        os.makedirs(directory, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        filename = (
            f"{timestamp}_"
            f"{report_data['scanner_name']}.txt"
        )

        filepath = os.path.join(directory, filename)

        report = self.generate_report(report_data)

        with open(filepath, "w") as file:
            file.write(report)

    def find_previous_reports(self, domain):

        directory = f"./link_reports/{domain}"

        if not os.path.exists(directory):
            return []

        reports = sorted(os.listdir(directory))

        return reports

    # Main orchestration function
    async def scan_link(self, url, user):

        report_data = {

            "original_url": "",
            "final_url": "",
            "domain": "",
            "ip_address": "",
            "status_code": "",
            "redirect_history": [],
            "uses_https": False,

            "risk_score": "",
            "risk_reason": "",

            "virus_total": {
                "malicious": 0,
                "suspicious": 0,
                "harmless": 0,
                "undetected": 0,
                "flagged_vendors": []
            },

            "safe_browsing": {
                "safe": True,
                "api_success": True,
                "threats": []
            },

            "scan_date": "",
            "scanner_name": "",
            "scanner_id": ""

        }

        report_data["original_url"] = self.normalize_url(url)
        report_data["scanner_name"] = user.name
        report_data["scanner_id"] = user.id
        report_data["scan_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        await self.expand_url(report_data)

        # Don't continue if URL expansion failed.
        if report_data["status_code"] == None:
            self.save_report(report_data)
            return report_data

        self.get_domain_and_ip(report_data)

        await self.check_google_safe_browsing(report_data)

        await self.check_virus_total(report_data)

        self.calculate_risk_score(report_data)

        self.save_report(report_data)

        return report_data



