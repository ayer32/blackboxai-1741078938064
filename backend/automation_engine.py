from typing import Dict, List, Any, Optional
import aiohttp
import asyncio
from datetime import datetime
import json
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from microsoft.graph import GraphServiceClient
from O365 import Account
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import yaml
from fastapi import HTTPException

class AutomationEngine:
    def __init__(self):
        self.workflows = {}
        self.integrations = {}
        self.load_workflows()
        self.setup_integrations()

    def load_workflows(self):
        """Load custom workflows from storage"""
        workflow_path = "workflows"
        if not os.path.exists(workflow_path):
            os.makedirs(workflow_path)
        
        for filename in os.listdir(workflow_path):
            if filename.endswith('.yaml'):
                with open(os.path.join(workflow_path, filename), 'r') as f:
                    workflow = yaml.safe_load(f)
                    self.workflows[workflow['name']] = workflow

    def setup_integrations(self):
        """Initialize third-party service integrations"""
        self.integrations = {
            'google': self.setup_google_integration(),
            'microsoft': self.setup_microsoft_integration(),
            'spotify': self.setup_spotify_integration(),
            'ifttt': self.setup_ifttt_integration()
        }

    def setup_google_integration(self):
        """Set up Google Workspace integration"""
        SCOPES = [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = None
        token_path = 'token/google_token.json'
        
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials/google_credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
                
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
                
        return {
            'calendar': build('calendar', 'v3', credentials=creds),
            'gmail': build('gmail', 'v1', credentials=creds),
            'drive': build('drive', 'v3', credentials=creds)
        }

    def setup_microsoft_integration(self):
        """Set up Microsoft 365 integration"""
        client_id = os.getenv('MS_CLIENT_ID')
        client_secret = os.getenv('MS_CLIENT_SECRET')
        tenant_id = os.getenv('MS_TENANT_ID')
        
        account = Account((client_id, client_secret))
        if not account.is_authenticated:
            account.authenticate()
            
        return {
            'outlook': account.outlook(),
            'calendar': account.calendar(),
            'onedrive': account.storage()
        }

    def setup_spotify_integration(self):
        """Set up Spotify integration"""
        return spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=os.getenv('SPOTIFY_CLIENT_ID'),
            client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
            redirect_uri=os.getenv('SPOTIFY_REDIRECT_URI'),
            scope='user-modify-playback-state user-read-playback-state playlist-modify-public'
        ))

    def setup_ifttt_integration(self):
        """Set up IFTTT integration"""
        return {
            'key': os.getenv('IFTTT_KEY'),
            'base_url': 'https://maker.ifttt.com/trigger/{}/with/key/'
        }

    async def execute_workflow(self, workflow_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow by name"""
        if workflow_name not in self.workflows:
            raise HTTPException(status_code=404, detail=f"Workflow '{workflow_name}' not found")

        workflow = self.workflows[workflow_name]
        results = {}

        try:
            for step in workflow['steps']:
                result = await self.execute_step(step, params)
                results[step['name']] = result
                
                # Update params with step results for subsequent steps
                if 'output' in step:
                    params[step['output']] = result

            return {
                'success': True,
                'workflow': workflow_name,
                'results': results
            }
        except Exception as e:
            return {
                'success': False,
                'workflow': workflow_name,
                'error': str(e)
            }

    async def execute_step(self, step: Dict[str, Any], params: Dict[str, Any]) -> Any:
        """Execute a single workflow step"""
        service = step['service']
        action = step['action']
        
        if service == 'google':
            return await self.execute_google_action(action, step.get('params', {}), params)
        elif service == 'microsoft':
            return await self.execute_microsoft_action(action, step.get('params', {}), params)
        elif service == 'spotify':
            return await self.execute_spotify_action(action, step.get('params', {}), params)
        elif service == 'ifttt':
            return await self.execute_ifttt_action(action, step.get('params', {}), params)
        else:
            raise ValueError(f"Unknown service: {service}")

    async def execute_google_action(self, action: str, step_params: Dict[str, Any], workflow_params: Dict[str, Any]) -> Any:
        """Execute Google Workspace actions"""
        if action == 'create_calendar_event':
            event = {
                'summary': self.parse_param(step_params['summary'], workflow_params),
                'start': {'dateTime': self.parse_param(step_params['start_time'], workflow_params)},
                'end': {'dateTime': self.parse_param(step_params['end_time'], workflow_params)},
            }
            return self.integrations['google']['calendar'].events().insert(
                calendarId='primary', body=event).execute()
        
        elif action == 'send_email':
            message = {
                'to': self.parse_param(step_params['to'], workflow_params),
                'subject': self.parse_param(step_params['subject'], workflow_params),
                'body': self.parse_param(step_params['body'], workflow_params)
            }
            return self.integrations['google']['gmail'].users().messages().send(
                userId='me', body=message).execute()

    async def execute_microsoft_action(self, action: str, step_params: Dict[str, Any], workflow_params: Dict[str, Any]) -> Any:
        """Execute Microsoft 365 actions"""
        if action == 'create_calendar_event':
            event = {
                'subject': self.parse_param(step_params['subject'], workflow_params),
                'start': {'dateTime': self.parse_param(step_params['start_time'], workflow_params)},
                'end': {'dateTime': self.parse_param(step_params['end_time'], workflow_params)}
            }
            return self.integrations['microsoft']['calendar'].create_event(event)
        
        elif action == 'send_email':
            message = {
                'to_recipients': [{'emailAddress': {'address': self.parse_param(step_params['to'], workflow_params)}}],
                'subject': self.parse_param(step_params['subject'], workflow_params),
                'body': {'content': self.parse_param(step_params['body'], workflow_params)}
            }
            return self.integrations['microsoft']['outlook'].send_mail(message)

    async def execute_spotify_action(self, action: str, step_params: Dict[str, Any], workflow_params: Dict[str, Any]) -> Any:
        """Execute Spotify actions"""
        spotify = self.integrations['spotify']
        
        if action == 'play_playlist':
            playlist_name = self.parse_param(step_params['playlist'], workflow_params)
            playlists = spotify.current_user_playlists()
            playlist_id = next(
                (p['id'] for p in playlists['items'] if p['name'] == playlist_name),
                None
            )
            if playlist_id:
                return spotify.start_playback(context_uri=f'spotify:playlist:{playlist_id}')
        
        elif action == 'control_playback':
            command = self.parse_param(step_params['command'], workflow_params)
            if command == 'play':
                return spotify.start_playback()
            elif command == 'pause':
                return spotify.pause_playback()
            elif command == 'next':
                return spotify.next_track()
            elif command == 'previous':
                return spotify.previous_track()

    async def execute_ifttt_action(self, action: str, step_params: Dict[str, Any], workflow_params: Dict[str, Any]) -> Any:
        """Execute IFTTT actions"""
        async with aiohttp.ClientSession() as session:
            url = self.integrations['ifttt']['base_url'] + self.integrations['ifttt']['key']
            event_name = self.parse_param(step_params['event'], workflow_params)
            
            payload = {
                'value1': self.parse_param(step_params.get('value1', ''), workflow_params),
                'value2': self.parse_param(step_params.get('value2', ''), workflow_params),
                'value3': self.parse_param(step_params.get('value3', ''), workflow_params)
            }
            
            async with session.post(f"{url}/{event_name}", json=payload) as response:
                return await response.json()

    def parse_param(self, param: str, workflow_params: Dict[str, Any]) -> str:
        """Parse parameter values, replacing variables with actual values"""
        if not isinstance(param, str):
            return param
            
        for key, value in workflow_params.items():
            param = param.replace(f"${key}", str(value))
        return param

    async def create_workflow(self, workflow_def: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new custom workflow"""
        name = workflow_def['name']
        if name in self.workflows:
            raise HTTPException(status_code=400, detail=f"Workflow '{name}' already exists")
            
        workflow_path = os.path.join('workflows', f"{name}.yaml")
        with open(workflow_path, 'w') as f:
            yaml.dump(workflow_def, f)
            
        self.workflows[name] = workflow_def
        return {'success': True, 'message': f"Workflow '{name}' created successfully"}

    async def update_workflow(self, workflow_def: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing workflow"""
        name = workflow_def['name']
        if name not in self.workflows:
            raise HTTPException(status_code=404, detail=f"Workflow '{name}' not found")
            
        workflow_path = os.path.join('workflows', f"{name}.yaml")
        with open(workflow_path, 'w') as f:
            yaml.dump(workflow_def, f)
            
        self.workflows[name] = workflow_def
        return {'success': True, 'message': f"Workflow '{name}' updated successfully"}

    async def delete_workflow(self, name: str) -> Dict[str, Any]:
        """Delete a workflow"""
        if name not in self.workflows:
            raise HTTPException(status_code=404, detail=f"Workflow '{name}' not found")
            
        workflow_path = os.path.join('workflows', f"{name}.yaml")
        os.remove(workflow_path)
        del self.workflows[name]
        
        return {'success': True, 'message': f"Workflow '{name}' deleted successfully"}

    def get_workflows(self) -> List[Dict[str, Any]]:
        """Get all available workflows"""
        return list(self.workflows.values())

    def get_workflow(self, name: str) -> Dict[str, Any]:
        """Get a specific workflow by name"""
        if name not in self.workflows:
            raise HTTPException(status_code=404, detail=f"Workflow '{name}' not found")
        return self.workflows[name]
