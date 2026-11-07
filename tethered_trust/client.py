"""Tethered Trust client for Python 3.8+. Standard library only.

    from tethered_trust import TetheredTrust
    tt = TetheredTrust(sandbox=True)            # sandbox: free, never charged
    plan = tt.validate_plan({"setup": ["Lenovo ThinkPad T480"],
                             "purchase": [{"text": "Crucial CT16G4SFRA32A", "quantity": 2}]})
    if plan["decision"] == "insufficient_evidence":
        print(plan["questions"])

Download: https://tetheredtrust.com/sdk/tethered_trust.py
"""
import json
import time
import urllib.error
import urllib.parse
import urllib.request

# Every MCP tool as (method, path); call(name, args) reaches any of them.
TOOLS = {"how_it_works":["GET","/how-it-works"],"list_coverage":["GET","/coverage"],"check_cart_before_checkout":["POST","/checkout/check"],"enrich_catalog":["POST","/enrich"],"identify_product":["POST","/identify"],"list_standards":["GET","/standards"],"resolve_product":["GET","/resolve"],"validate_purchase_plan":["POST","/plan"],"fix_purchase_plan":["POST","/plan/fix"],"plan_upgrade":["POST","/upgrades"],"identify_from_photo":["POST","/identify/photo"],"recheck_plan":["POST","/plans/recheck"],"check_batch":["POST","/check/batch"],"check_compatibility":["POST","/check"],"find_parts":["POST","/parts"],"check_recalls":["POST","/recalls"],"verify_page":["POST","/verify"],"verify_mcp":["POST","/verify/mcp"],"watch_decision":["POST","/watch"],"attach_order":["POST","/receipts/attach"],"dispute_packet":["POST","/packet"],"file_claim":["POST","/claims"],"decision_status":["POST","/watch/status"],"check_fit":["POST","/fit"],"verify_receipt":["POST","/receipts/verify"],"report_outcome":["POST","/outcome"]}


class TetheredTrustError(Exception):
    def __init__(self, status, body):
        super().__init__(body.get("error") if isinstance(body, dict) else f"HTTP {status}")
        self.status = status
        self.body = body
        self.code = body.get("code") if isinstance(body, dict) else None
        self.retryable = bool(body.get("retryable")) if isinstance(body, dict) else False
        self.retry_after_seconds = body.get("retry_after_seconds") if isinstance(body, dict) else None


class TetheredTrust:
    def __init__(self, api_key=None, base_url="https://tetheredtrust.com", sandbox=False, timeout=30, retries=1):
        self.api_key = api_key
        self.root = base_url.rstrip("/") + ("/v1/sandbox" if sandbox else "/v1")
        self.timeout = timeout
        self.retries = retries

    def call(self, tool, args=None):
        """Any tool by its MCP name, e.g. call("check_cart_before_checkout", {"owned": [...], "line_items": [...]})."""
        method, path = TOOLS[tool]
        args = args or {}
        if method == "GET":
            return self.request("GET", path + ("?" + urllib.parse.urlencode(args) if args else ""))
        return self.request("POST", path, args)

    def request(self, method, path, body=None, _attempt=0):
        """Retries once on retryable errors (429, 503, 5xx), honoring retry_after_seconds up to 10 s. Never retries 402."""
        try:
            return self._request(method, path, body)
        except TetheredTrustError as e:
            if e.retryable and e.status != 402 and _attempt < self.retries:
                time.sleep(min(10, e.retry_after_seconds if e.retry_after_seconds is not None else 2))
                return self.request(method, path, body, _attempt + 1)
            raise

    def _request(self, method, path, body=None):
        headers = {"Content-Type": "application/json", "User-Agent": "tethered-trust-python/0.51.2"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.root + path, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as res:
                return json.loads(res.read().decode())
        except urllib.error.HTTPError as e:
            try:
                payload = json.loads(e.read().decode())
            except Exception:
                payload = {"error": f"HTTP {e.code}"}
            raise TetheredTrustError(e.code, payload) from None

    def validate_plan(self, plan):
        """Whole setup + cart -> decision, results, system_checks, required_accessories, substitutions, questions, receipt."""
        return self.request("POST", "/plan", plan)

    def recheck_plan(self, plan_id):
        return self.request("POST", "/plans/recheck", {"plan_id": plan_id})

    def get_plan(self, plan_id):
        return self.request("GET", "/plans/" + urllib.parse.quote(plan_id))

    def check(self, existing, candidate, **extra):
        return self.request("POST", "/check", {"existing": existing, "candidate": candidate, **extra})

    def check_batch(self, checks):
        return self.request("POST", "/check/batch", {"checks": checks})

    def find_parts(self, model, part_type=None):
        return self.request("POST", "/parts", {"model": model, "part_type": part_type})

    def resolve(self, query):
        return self.request("GET", "/resolve?query=" + urllib.parse.quote(query))

    def suggest(self, q, role="any"):
        return self.request("GET", "/suggest?" + urllib.parse.urlencode({"q": q, "role": role}))

    def verify_receipt(self, jws_or_id):
        body = {"receipt_id": jws_or_id} if str(jws_or_id).startswith("rcpt_") else {"jws": jws_or_id}
        return self.request("POST", "/receipts/verify", body)

    def report_outcome(self, check_id, outcome, evidence=None):
        return self.request("POST", "/outcome", {"check_id": check_id, "outcome": outcome, "evidence": evidence})

    def usage(self):
        return self.request("GET", "/usage")

    def check_cart(self, checkout_input):
        return self.request("POST", "/checkout/check", checkout_input)

    def identify(self, product, **extra):
        return self.request("POST", "/identify", {"product": product, **extra})

    def standards(self):
        return self.request("GET", "/standards")

    def upgrades(self, model, goal=None):
        return self.request("POST", "/upgrades", {"model": model, "goal": goal})

    def fix_plan(self, plan):
        return self.request("POST", "/plan/fix", plan)

    def fit(self, fit_input):
        return self.request("POST", "/fit", fit_input)

    def enrich(self, items, **extra):
        return self.request("POST", "/enrich", {"items": items, **extra})

    def identify_photo(self, photo_input):
        return self.request("POST", "/identify/photo", photo_input)

    def coverage(self, category=None):
        return self.request("GET", "/coverage" + ("?category=" + urllib.parse.quote(category) if category else ""))
