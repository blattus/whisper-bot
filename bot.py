
from typing import AsyncIterable

import os
import fal_client
import fastapi_poe as fp
import httpx
from dotenv import load_dotenv
load_dotenv()

POE_ACCESS_KEY = os.getenv("POE_ACCESS_KEY")
FAL_KEY = os.getenv("FAL_KEY")


class TranscriptMaker(fp.PoeBot):
    def __post_init__(self) -> None:
        super().__post_init__()
        self.fal_client = fal_client.AsyncClient(key=FAL_KEY)
        self.http_client = httpx.AsyncClient()
    
    async def get_response(
        self, request: fp.QueryRequest
    ) -> AsyncIterable[fp.PartialResponse]:
        yield fp.MetaResponse(
            text="",
            content_type="text/markdown",
            linkify=True,
            refetch_settings=False,
            suggested_replies=False,
        )
        
        message = request.query[-1]
        print(message)

        # echo test
        # yield fp.PartialResponse(text=message.content)

        # print the message content
        print('-----------')
        print(message.content)
        print('-----------')
        
        # check if the message contains an attachment; if so, check if it is an audio file
        if message.attachments:
            # check if the attachment is an audio file by checking the content type
            if message.attachments[0].content_type == "audio/mpeg":
                audio_url = message.attachments[0].url
                print(audio_url)

                yield fp.PartialResponse(text="Audio file detected! Generating transcript, please wait...")
                handler = await self.fal_client.submit(
                    "fal-ai/whisper",
                    arguments={
                        "audio_url": audio_url
                    },
                )

                data = await handler.get()
                print(data)

                yield fp.PartialResponse(text="Transcript generated!", is_replace_response=True)
                yield fp.PartialResponse(text=data['text'], is_replace_response=True)
            else:
                print("attachment is not an audio file")
                yield fp.PartialResponse(text="Please provide an audio file as an attachment.")
                return


        # check if the message contains a url by checking if it starts with http
        if message.content.startswith("http"):
            # check if the url is an audio file by checking the end of the url
            if message.content.endswith(".mp3") or message.content.endswith(".wav"):
                audio_url = message.content
                print(audio_url)

                yield fp.PartialResponse(text="Audio file detected! Generating transcript, please wait...")
                handler = await self.fal_client.submit(
                    "fal-ai/whisper",
                    arguments={
                        "audio_url": audio_url
                    },
                )

                data = await handler.get()
                print(data)

                yield fp.PartialResponse(text="Transcript generated!", is_replace_response=True)
                yield fp.PartialResponse(text=data['text'], is_replace_response=True)

            else:
                print("url starts with http but not an audio file")
                yield fp.PartialResponse(text="Please provide a link to an audio file (URL should end in .mp3 or .wav)")
                return
        # else:
        #     print("no url provided")
        #     yield fp.PartialResponse(text="Please provide a url linking to an audio file (beginning with http).")
        #     return
            
    
    async def get_settings(self, setting: fp.SettingsRequest) -> fp.SettingsResponse:
        return fp.SettingsResponse(
            allow_attachments=True,
            introduction_message=(
                "Welcome to the transcript maker! Please attach an audio file "
                "or URL and I'll help transcribe it for you"
            ),
        )
    
bot = TranscriptMaker()
app = fp.make_app(bot, POE_ACCESS_KEY)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
