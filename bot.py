import asyncpraw
import os
import asyncio
import aiohttp
import time

from dotenv import load_dotenv

load_dotenv()

# env vars
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
USER_HANDLE = os.getenv('USER_HANDLE')
USER_PASSWORD = os.getenv('USER_PASSWORD')
BOT_SUBREDDIT = os.getenv('BOT_SUBREDDIT')
OPENAI_URL = os.getenv('OPENAI_URL')
OPENAI_BEARER_TOKEN = os.getenv('OPENAI_BEARER_TOKEN')
OPENAI_TEXT_MODEL = 'text-curie-001'
OPENAI_CODE_MODEL = 'code-davinci-002'
SLEEP_TIME = 5
SKIP_EXISTING = False

# setup OpenAI request
openai = {
  'url': OPENAI_URL,
  'headers': {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {OPENAI_BEARER_TOKEN}',
  },
}

async def main():
  # setup Reddit client
  async with asyncpraw.Reddit(
    client_id = CLIENT_ID,
    client_secret = CLIENT_SECRET,
    user_agent = 'OpenAI Reddit Bot',
    username = USER_HANDLE,
    password = USER_PASSWORD,
  ) as reddit :
    me = await reddit.user.me()
    subreddits = await reddit.subreddit(f'{BOT_SUBREDDIT}')

    print('=============================')
    print('Logged in as:', me)
    print('Replying in:', f'/r/{subreddits.display_name}')
    print('=============================')

    # create concurrent tasks for submission and comment processors
    task1 = asyncio.create_task(process_comments(subreddits, me))
    task2 = asyncio.create_task(process_submissions(subreddits, me))

    await task1
    await task2

# submission processor
async def process_submissions(subreddits, user) :
  async for submission in subreddits.stream.submissions(skip_existing = SKIP_EXISTING) :
    content = submission.selftext.lower()
    not_me = submission.author != user

    # reply to submission if author is not me
    res = await openai_text(content)
    if res and not_me :
      start = time.time()
      await submission.reply(res)
      print('=============================')
      print(f'Replied to Submission by: {submission.author}')
      end = time.time()
      print(f'Time to reply: {round(end - start, 2)}s')
      print('=============================')

# comment processor
async def process_comments(subreddits, user) :
  async for comment in subreddits.stream.comments(skip_existing = SKIP_EXISTING) :
    content = comment.body.lower()
    not_me = comment.author != user

    # check if keyword is in comment and author is not me
    res = await openai_text(content)
    if res and not_me :
      start = time.time()
      await comment.reply(res)
      print('=============================')
      print(f'Replied to Comment by: {comment.author}')
      end = time.time()
      print(f'Time to reply: {round(end - start, 2)}s')
      print('=============================')

# process text comment through OpenAI
async def openai_text(input) :
  payload = {
    'model': OPENAI_TEXT_MODEL,
    'prompt': f'{input}. Please reply in Markdown format that is appropriate for Reddit.',
    'max_tokens': 256,
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
    async with session.post(url, json = payload, headers = headers) as res:
      output = await res.json()
      disclaimer = '\n\n\n---\n\n*^Beep ^boop! ^I ^am ^a ^bot ^that ^replies ^using ^the ^[OpenAI](https://openai.com/api/) ^api. ^Please ^contact ^/u/metalandcode ^if ^you ^have ^any ^questions.*'
      
      # ensure response is valid
      if output and output['choices'][0] :
        reply = output['choices'][0]['text'].strip()
        return f'{reply}{disclaimer}'
      else :
        return f'I am sorry! I was unable to process your query at this time!{disclaimer}'

# run bot
if __name__ == "__main__":
  asyncio.run(main())
