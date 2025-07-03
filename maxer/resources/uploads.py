from typing import Any, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.client import MaxerClient


class UploadsAPI:
    def __init__(self, client: "MaxerClient"):
        self._c = client

    async def get_url(self, file_type: str) -> str:
        return await self._c.get_upload_url(file_type)

    async def upload_file(self, path, file_type: str) -> Dict[str, Any]:
        return await self._c.upload_file(path, file_type)

    async def upload_video(self, path):
        return await self._c.upload_video(path)

    # ----------------------- Convenience helpers -----------------------
    async def upload_image(self, path):
        return await self._c.upload_file(path, "image")

    async def upload_audio(self, path):
        return await self._c.upload_file(path, "audio")

    async def upload_document(self, path):
        return await self._c.upload_file(path, "file")

    upload = upload_file 