import aiohttp
from datetime import datetime


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
        async with self.session.get(report_data["original_url"], timeout=self.timeout) as response:
            report_data["final_url"] = str(response.url)
            report_data["status_code"] = response.status

    async def check_virus_total(self, report_data: dict):
        ...

    async def check_google_safe_browsing(self, report_data: dict):
        ...

    # Regular helper functions
    # Turns the URL given into a universal URL. http:// or https://
    def normalize_url(self, url):
        url = url.strip()

        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"
        return url


    def calculate_risk_score(self, report):
        ...

    def generate_report(self, report):
        ...

    def save_report(self, report):
        ...

    def find_previous_reports(self, url):
        ...

    # Main orchestration function
    async def scan_link(self, url, user):
        report_data = {

            "original_url": "",
            "final_url": "",
            "status_code": "",
            "redirect_history": [],
            "risk_score": "",
            "virus_total": {},
            "safe_browsing": {},
            "scan_date": "",
            "scanner_name": "",
            "scanner_id": ""

        }

        report_data["original_url"] = self.normalize_url(url)
        report_data["scanner_name"] = user.name
        report_data["scanner_id"] = user.id
        report_data["scan_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        await self.expand_url(report_data)
        await self.check_google_safe_browsing(report_data)
        await self.check_virus_total(report_data)

        self.calculate_risk_score(report_data)
        self.generate_report(report_data)
        self.save_report(report_data)

        return report_data



