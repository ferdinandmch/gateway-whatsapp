from abc import ABC, abstractmethod

from app.schemas.provider import MessageType, ProviderResult


class MessagingProvider(ABC):

    @abstractmethod
    async def create_instance(self, instance_name: str) -> ProviderResult: ...

    @abstractmethod
    async def get_instance_status(self, instance_name: str) -> ProviderResult: ...

    @abstractmethod
    async def connect_instance(self, instance_name: str) -> ProviderResult: ...

    @abstractmethod
    async def disconnect_instance(self, instance_name: str) -> ProviderResult: ...

    @abstractmethod
    async def delete_instance(self, instance_name: str) -> ProviderResult: ...

    @abstractmethod
    async def send_text(
        self, instance_name: str, to: str, content: str
    ) -> ProviderResult: ...

    @abstractmethod
    async def send_media(
        self,
        instance_name: str,
        to: str,
        media_type: MessageType,
        media_url: str,
        caption: str | None = None,
        filename: str | None = None,
    ) -> ProviderResult: ...
