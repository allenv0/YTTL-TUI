# SPDX-License-Identifier: Apache-2.0

import requests
import json
import aiohttp
import asyncio

BASE_URL = 'https://huggingface.co/chat'
HEADERS = {
    'content-type': 'application/json'
}

class TooManyRequestsError(Exception):
    pass

class HuggingchatSession(object):
    def __init__(self, model):
        self.model = model
        settings = {
            'searchEnabled': True,
            'ethicsModalAccepted': True,
            'ethicsModalAcceptedAt': None,
            'activeModel': model,
            'hideEmojiOnSidebar': False,
            'shareConversationsWithModelAuthors': False,
            'customPrompts': {},
            'assistants': [],
            'recentlySaved': False
        }
        resp = requests.post(f'{BASE_URL}/settings', headers=HEADERS, data=json.dumps(settings))
        resp.raise_for_status()
        self.cookies = resp.cookies
    
    def send_request(self, prompt):
        start_convo_req = {
            'model': self.model,
            'preprompt': ''
        }
        start_convo_resp = requests.post(f'{BASE_URL}/conversation', headers=HEADERS, cookies=self.cookies, data=json.dumps(start_convo_req))
        start_convo_resp.raise_for_status()
        convo_id = start_convo_resp.json()['conversationId']
        svetle_resp = requests.get(f'{BASE_URL}/conversation/{convo_id}/__data.json?x-sveltekit-invalidated=11', cookies=self.cookies)
        svetle_resp.raise_for_status()
        sjs = svetle_resp.json()
        data = sjs['nodes'][-1]['data']
        msgs = data[data[0]['messages']]
        msg = data[msgs[0]]
        msg_id = data[msg['id']]
        convo_req = {
            'inputs': prompt,
            'id': msg_id,
            'is_retry': False,
            'is_continue': False,
            'web_search': False,
            'files': []
        }
        convo_resp = requests.post(f'{BASE_URL}/conversation/{convo_id}', cookies=self.cookies, data=json.dumps(convo_req), headers=HEADERS)
        if convo_resp.status_code == 429:
            raise TooManyRequestsError()
        convo_resp.raise_for_status()
        events = convo_resp.text.split('\n')
        for event in events:
            ejs = json.loads(event)
            if ejs['type'] == 'finalAnswer':
                return ejs['text']
        raise Exception('Has not received final answer')


class AsyncHuggingchatSession(object):
    def __init__(self, model):
        self.model = model
        self.cookies = None
    
    async def initialize(self):
        """Initialize session asynchronously"""
        settings = {
            'searchEnabled': True,
            'ethicsModalAccepted': True,
            'ethicsModalAcceptedAt': None,
            'activeModel': self.model,
            'hideEmojiOnSidebar': False,
            'shareConversationsWithModelAuthors': False,
            'customPrompts': {},
            'assistants': [],
            'recentlySaved': False
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f'{BASE_URL}/settings', headers=HEADERS, 
                                  data=json.dumps(settings)) as resp:
                resp.raise_for_status()
                self.cookies = resp.cookies
    
    async def send_request_async(self, prompt):
        """Send async request to HuggingChat"""
        if self.cookies is None:
            await self.initialize()
        
        start_convo_req = {
            'model': self.model,
            'preprompt': ''
        }
        
        async with aiohttp.ClientSession(cookies=self.cookies) as session:
            # Start conversation
            async with session.post(f'{BASE_URL}/conversation', headers=HEADERS, 
                                  data=json.dumps(start_convo_req)) as resp:
                if resp.status == 429:
                    raise TooManyRequestsError()
                resp.raise_for_status()
                convo_data = await resp.json()
                convo_id = convo_data['conversationId']
            
            # Get conversation data
            async with session.get(f'{BASE_URL}/conversation/{convo_id}/__data.json?x-sveltekit-invalidated=11') as resp:
                resp.raise_for_status()
                sjs = await resp.json()
                data = sjs['nodes'][-1]['data']
                msgs = data[data[0]['messages']]
                msg = data[msgs[0]]
                msg_id = data[msg['id']]
            
            # Send message
            convo_req = {
                'inputs': prompt,
                'id': msg_id,
                'is_retry': False,
                'is_continue': False,
                'web_search': False,
                'files': []
            }
            
            async with session.post(f'{BASE_URL}/conversation/{convo_id}', 
                                  data=json.dumps(convo_req), headers=HEADERS) as resp:
                if resp.status == 429:
                    raise TooManyRequestsError()
                resp.raise_for_status()
                text = await resp.text()
                
                events = text.split('\n')
                for event in events:
                    if event.strip():
                        try:
                            ejs = json.loads(event)
                            if ejs['type'] == 'finalAnswer':
                                return ejs['text']
                        except json.JSONDecodeError:
                            continue
                
                raise Exception('Has not received final answer')
