import httpx

from app.core.phone import normalize_phone
from app.providers.base import MessagingProvider
from app.schemas.provider import InstanceState, MessageType, ProviderError, ProviderResult

_STATE_MAP = {
    "open": InstanceState.connected,
    "close": InstanceState.disconnected,
    "connecting": InstanceState.connecting,
    "qrcode": InstanceState.connecting,
}


class EvolutionProvider(MessagingProvider):

    def __init__(
        self,
        base_url: str,
        api_key: str,
        webhook_base_url: str,
        webhook_secret: str = "",
        timeout: int = 30,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._webhook_base_url = webhook_base_url.rstrip("/")
        self._webhook_secret = webhook_secret
        self._timeout = timeout

    async def _make_request(
        self,
        method: str,
        path: str,
        json: dict | None = None,
    ) -> ProviderResult:
        url = f"{self._base_url}{path}"
        headers = {"apikey": self._api_key}
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.request(method, url, headers=headers, json=json)
        except httpx.TimeoutException:
            return ProviderResult(
                success=False,
                error=ProviderError(code="PROVIDER_TIMEOUT", message="Request timed out"),
            )
        except httpx.ConnectError:
            return ProviderResult(
                success=False,
                error=ProviderError(code="PROVIDER_UNAVAILABLE", message="Could not connect to provider"),
            )

        if response.status_code == 404:
            return ProviderResult(
                success=False,
                error=ProviderError(code="INSTANCE_NOT_FOUND", message="Instance not found"),
            )
        if response.status_code == 409:
            return ProviderResult(
                success=False,
                error=ProviderError(code="INSTANCE_ALREADY_EXISTS", message="Instance already exists"),
            )
        if response.status_code == 400:
            return ProviderResult(
                success=False,
                error=ProviderError(code="INVALID_REQUEST", message="Invalid request"),
            )
        if response.status_code >= 500:
            return ProviderResult(
                success=False,
                error=ProviderError(code="PROVIDER_ERROR", message=f"Provider error: {response.status_code}"),
            )

        try:
            data = response.json()
        except Exception:
            return ProviderResult(
                success=False,
                error=ProviderError(code="UNEXPECTED_RESPONSE", message="Could not parse provider response"),
            )

        return ProviderResult(success=True, data=data)

    async def create_instance(self, instance_name: str) -> ProviderResult:
        result = await self._make_request(
            "POST",
            "/instance/create",
            json={
                "instanceName": instance_name,
                "integration": "WHATSAPP-BAILEYS",
            },
        )
        if not result.success:
            return result

        webhook_url = f"{self._webhook_base_url}/v1/webhooks/evolution/{instance_name}"
        webhook_payload: dict = {
            "enabled": True,
            "url": webhook_url,
            "webhookByEvents": False,
            "webhookBase64": False,
            "events": [
                "MESSAGES_UPSERT",
                "MESSAGES_UPDATE",
                "CONNECTION_UPDATE",
                "SEND_MESSAGE",
            ],
        }
        if self._webhook_secret:
            webhook_payload["headers"] = {"X-Webhook-Secret": self._webhook_secret}
        await self._make_request(
            "POST",
            f"/webhook/set/{instance_name}",
            json={"webhook": webhook_payload},
        )

        return ProviderResult(success=True, data={"instance_name": instance_name})

    async def get_instance_status(self, instance_name: str) -> ProviderResult:
        result = await self._make_request("GET", f"/instance/connectionState/{instance_name}")
        if not result.success:
            if result.error and result.error.code == "INSTANCE_NOT_FOUND":
                return ProviderResult(success=True, data={"state": InstanceState.not_found})
            return result
        raw_state = (result.data or {}).get("instance", {}).get("state", "")
        state = _STATE_MAP.get(raw_state, InstanceState.disconnected)
        return ProviderResult(success=True, data={"state": state})

    async def connect_instance(self, instance_name: str) -> ProviderResult:
        result = await self._make_request("GET", f"/instance/connect/{instance_name}")
        if not result.success:
            return result
        data = result.data or {}
        return ProviderResult(
            success=True,
            data={
                "qrcode": data.get("base64") or data.get("qrcode"),
                "pairingCode": data.get("pairingCode") or data.get("code"),
            },
        )

    async def disconnect_instance(self, instance_name: str) -> ProviderResult:
        result = await self._make_request("DELETE", f"/instance/logout/{instance_name}")
        if not result.success:
            return result
        return ProviderResult(success=True, data={"instance_name": instance_name})

    async def delete_instance(self, instance_name: str) -> ProviderResult:
        result = await self._make_request("DELETE", f"/instance/delete/{instance_name}")
        if not result.success:
            return result
        return ProviderResult(success=True, data={"instance_name": instance_name})

    async def send_text(self, instance_name: str, to: str, content: str) -> ProviderResult:
        number = normalize_phone(to)
        result = await self._make_request(
            "POST",
            f"/message/sendText/{instance_name}",
            json={"number": number, "text": content},
        )
        if not result.success:
            return result
        message_id = (result.data or {}).get("key", {}).get("id") or (result.data or {}).get("id")
        return ProviderResult(success=True, data={"provider_message_id": message_id})

    async def send_media(
        self,
        instance_name: str,
        to: str,
        media_type: MessageType,
        media_url: str,
        caption: str | None = None,
        filename: str | None = None,
    ) -> ProviderResult:
        number = normalize_phone(to)
        payload: dict = {"number": number, "mediatype": media_type.value, "media": media_url}
        if caption is not None:
            payload["caption"] = caption
        if filename is not None:
            payload["fileName"] = filename
        result = await self._make_request(
            "POST",
            f"/message/sendMedia/{instance_name}",
            json=payload,
        )
        if not result.success:
            return result
        message_id = (result.data or {}).get("key", {}).get("id") or (result.data or {}).get("id")
        return ProviderResult(success=True, data={"provider_message_id": message_id})
