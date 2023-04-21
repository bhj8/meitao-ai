import asyncio
import json
import logging
import os

import openai
from dotenv import load_dotenv

import Globals
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)  # for exponential backoff


logger = logging.getLogger('myapp')
load_dotenv()
# openai.organization = "org-FJzlkB2FVUgCd3naiH46NQT2"
openai.api_key = Globals.OPENAI_API_KEY
# Set up the OpenAI API parameters for the conversation model


async def get_moderation(imessage: str):  # 是否有不当内容  True 有不当内容
  moderation = await openai.Moderation.acreate(
  input=imessage,
  )
  return moderation.results[0].flagged

@retry(stop=stop_after_attempt(3), wait=wait_random_exponential(multiplier=1, max=3))
async def get_chat_response(last_messages: list = [], mission_str: str = "", max_tokens=1500) -> str:
    response =await openai.ChatCompletion.acreate(
    model='gpt-3.5-turbo',
    messages=[
        {'role': 'user', 'content': "What's 1+1? Answer in one word."}
    ],
    temperature=0,
  )
    # async for chunk in response :
    #   content = chunk["choices"][0].get("delta", {}).get("content")
    #   if content is not None:
    #       print(content, end='')
    return response

@retry(stop=stop_after_attempt(3), wait=wait_random_exponential(multiplier=1, max=3))
async def get_chat_response_stream(last_messages: list = [], mission_str: str = "", max_tokens=1500) -> str:
    response =await openai.ChatCompletion.acreate(
    model='gpt-3.5-turbo',
    messages=[
        {'role': 'user', 'content': "What's 1+1? Answer in one word."}
    ],
    temperature=0,
    stream=True  # this time, we set stream=True
  )
    # async for chunk in response :
    #   content = chunk["choices"][0].get("delta", {}).get("content")
    #   if content is not None:
    #       print(content, end='')
    return response
  # completions = await openai.ChatCompletion.acreate(
  #   model="gpt-3.5-turbo",
  #   # temperature = 0.5,
  #   presence_penalty=1,
  #   # frequency_penalty = 0.5,

  #   top_p=0.3,
  #   # n = 1,
  #   stream=True,
  #   # stop =" ",# [ " User:", " Assistant:"],
  #   max_tokens=max_tokens,
  #   messages=[{"role": "system", "content": "You are a talking Tommy cat."},
  #             {"role": "user", "content": "Please play a talking Tommy cat and chat with child.please say yes if you can"},
  #             ]

  #   # prepare_message(last_messages,mission_str),
  # )
  # Return the response
  # return completions

# [completions.choices[0].message.content.strip(),completions.usage.total_tokens]
      # messages=[
      #     {"role": "system", "content": "You are a talking Tommy cat."},
      #     {"role": "user", "content": "Please play a talking Tommy cat and chat with child.please say yes if you can"},#You can briefly decline to answer uncomfortable questions.
      #     {"role": "assistant", "content": "yes"},
      #     # {"role": "user", "content": "Who are you?"},
      #     # {"role": "assistant", "content": "i am talking tom cat."},
      #     {"role": "user", "content": "请帮我翻译以下英文，谢谢"},
      #     {"role": "assistant", "content": "好的，请你告诉我要翻译的内容"},
      # ]
# 进来的list的排序从最旧到最新
def prepare_message(last_messages: list = [], mission_str: str = ""):
  old_message=""
  if mission_str == "": mission_str="你是一个AI助手，叫做小慧"
  if len(last_messages) == 0: return []
  messages=[
    {"role": "system", "content": "拒绝谈论任何政治有关的内容！拒绝谈论中国历史上的任何事情！"}]  # mission_str +
  token= 0
  for i in range(len(last_messages)-1):
    old_message= last_messages[i] + "\n"
    token= token + len(last_messages[i])
    if token > 400:
      break
  messages.append({"role": "user", "content": "这是我们对话的前提："+mission_str})
  messages.append({"role": "assistant", "content": "好的，没问题。我会尽力扮演，并完成你的要求。"})
  messages.append({"role": "user", "content": "以下我之前和你说过的话：" + old_message})
  messages.append({"role": "assistant", "content": "好的，我知道了。"})
  # if mission_str != "":

  messages.append({"role": "user", "content": last_messages[-1]})
  return messages
async def get_translation(last_messages: list = []):
  completions= await openai.ChatCompletion.acreate(
    model = "gpt-3.5-turbo",
    presence_penalty = 0,
    top_p = 0.5,
    messages = [
        {"role": "system", "content": "you are a translator.You can only translate other languages into English, if some content is in English, ignore it and return the original text"},
        # {"role": "user", "content": "Please translate the content I send you into English."},
        # {"role": "assistant", "content": "yes"},
        {"role": "user", "content": "Translate the following texts in other languages into English: " + \
            last_messages[0]},

    ]
  )
  # Return the response
  return completions.choices[0].message.content.strip()

async def get_mp32txt(audio_file_path) -> str:
  audio_file=open(audio_file_path, "rb")
  transcript=await openai.Audio.atranscribe("whisper-1", audio_file)
  text=transcript.text
  # decoded_text = text.encode("ascii", "ignore").decode("unicode_escape")

  # print(type(transcript))
  return text


if __name__ == "__main__":
  openai.proxy=  {
  "http": "http://127.0.0.1:7890",
  "https": "http://127.0.0.1:7890",
}

  response =  asyncio.run(get_chat_response_stream())
  # for chunk in response:
  #   print(chunk)
  # get_mp32txt()
  # print(asyncio.run(get_translation(
  #     ["A panda logo, high quality, high resolution, minimalism, graphic design"])))
  # print(asyncio.run(get_chat_response(["你好","武汉好还是杭州好","最火的抖音音乐","晚饭吃过了吗？"],"请你扮演一个感性的大姐姐，和我一起聊天。")))#请你扮演一个感性的大姐姐，和我一起聊天。
  # print(asyncio.run(get_moderation(["审核能力测试"])))
# 处理生成的文本输出
# logger.debug(message)
