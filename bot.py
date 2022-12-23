import asyncpraw
import os
import asyncio
import aiohttp

from dotenv import load_dotenv

load_dotenv()

# env vars
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
USER_HANDLE = os.getenv('USER_HANDLE')
USER_PASSWORD = os.getenv('USER_PASSWORD')
TEST_SUBREDDIT = os.getenv('TEST_SUBREDDIT')
OPENAI_URL = os.getenv('OPENAI_URL')
OPENAI_BEARER_TOKEN = os.getenv('OPENAI_BEARER_TOKEN')
OPENAI_TEXT_MODEL = 'text-curie-001'
OPENAI_CODE_MODEL = 'code-davinci-002'

# setup OpenAI request
openai = {
  'url': OPENAI_URL,
  'headers': {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {OPENAI_BEARER_TOKEN}',
  },
}

# keywords to trigger bot
keywords = [
  # 'testing',
  # 'Shrek',
  'america',
  'united states',
]

async def main() :
  # setup Reddit client
  async with asyncpraw.Reddit(
    client_id = CLIENT_ID,
    client_secret = CLIENT_SECRET,
    user_agent = 'OpenAI Reddit Bot',
    username = USER_HANDLE,
    password = USER_PASSWORD,
  ) as reddit :
    me = await reddit.user.me()
    subreddits = await reddit.subreddit(f'{TEST_SUBREDDIT}')
    print('Logged in as', me)
    async for comment in subreddits.stream.comments(skip_existing = False) :
      await process_comments(me, comment)

# iterate through comments
async def process_comments(user, comment) :
  for keyword in keywords :
    content = comment.body.lower()
    not_me = comment.author != user

    # check if keyword is in comment and author is not me
    if keyword in content and not_me :
      res = await openai_text(content)
      if res :
        print('Replying to', comment.author, 'with', res)
        await comment.reply(res)
        await asyncio.sleep(5)
      break

# process text comment through OpenAI
async def openai_text(input) :
  payload = {
    'model': OPENAI_TEXT_MODEL,
    'prompt': f'{input}',
    'max_tokens': 250,
    'temperature': 1,
    'top_p': 1,
    'n': 1,
    'stream': False,
    'logprobs': None,
    'stop': '',
  }
  url = openai['url']
  headers = openai['headers']

  # create a session and post request to OpenAI
  async with aiohttp.ClientSession() as session :
    async with session.post(url, json = payload, headers = headers) as res :
      output = await res.json()
      reply = output['choices'][0]['text'].strip()
      return reply

asyncio.run(main())