import requests
import urlparse
import json
import os

# Set this to True to see client-server exchange
verbose = False

class Client(object):
    """
    Gym client to interface with gym_http_server
    """
    def __init__(self, remote_base):
        self.remote_base = remote_base

    def _parse_server_error_or_raise_for_status(self, resp):
        j = {}
        try:
            j = resp.json()
        except:
            # Most likely json parse failed because of network error, not server error (server
            # sends its errors in json). Don't let parse exception go up, but rather raise default
            # error.
            resp.raise_for_status()
        if resp.status_code != 200 and "message" in j:  # descriptive message from server side
            raise ValueError(j["message"])
        resp.raise_for_status()
        return j

    def _post_request(self, route, data):
        url = urlparse.urljoin(self.remote_base, route)
        if verbose: print( "POST {}\n{}".format(url, json.dumps(data)) )
        headers = {'Content-type': 'application/json'}
        resp = requests.post(urlparse.urljoin(self.remote_base, route),
                            data=json.dumps(data),
                            headers=headers)
        return self._parse_server_error_or_raise_for_status(resp)

    def _get_request(self, route):
        url = urlparse.urljoin(self.remote_base, route)
        if verbose: print("GET {}".format(url))
        resp = requests.get(url)
        return self._parse_server_error_or_raise_for_status(resp)
        
    def env_create(self, env_id):
        route = '/v1/envs/'
        data = {'env_id': env_id}
        resp = self._post_request(route, data)
        instance_id = resp['instance_id']
        return instance_id

    def env_list_all(self):
        route = '/v1/envs/'
        resp = self._get_request(route)
        all_envs = resp['all_envs']
        return all_envs

    def env_reset(self, instance_id):
        route = '/v1/envs/{}/reset/'.format(instance_id)
        resp = self._post_request(route, None)
        observation = resp['observation']
        return observation

    def env_step(self, instance_id, action, render):
        route = '/v1/envs/{}/step/'.format(instance_id)
        data = {'action': action, 'render': render}
        resp = self._post_request(route, data)
        observation = resp['observation']
        reward = resp['reward']
        done = resp['done']
        info = resp['info']
        return [observation, reward, done, info]

    def env_action_space_info(self, instance_id):
        route = '/v1/envs/{}/action_space/'.format(instance_id)
        resp = self._get_request(route)
        info = resp['info']
        return info

    def env_observation_space_info(self, instance_id):
        route = '/v1/envs/{}/observation_space/'.format(instance_id)
        resp = self._get_request(route)
        info = resp['info']
        return info

    def env_monitor_start(self, instance_id, directory,
                              force=False, resume=False):
        route = '/v1/envs/{}/monitor/start/'.format(instance_id)
        data = {'directory': directory,
                'force': force,
                'resume': resume}
        self._post_request(route, data)

    def env_monitor_close(self, instance_id):
        route = '/v1/envs/{}/monitor/close/'.format(instance_id)
        self._post_request(route, None)

    def upload(self, training_dir, algorithm_id=None, api_key=None):
        if not api_key:
            api_key = os.environ.get('OPENAI_GYM_API_KEY')

        route = '/v1/upload/'
        data = {'training_dir': training_dir,
                'algorithm_id': algorithm_id,
                'api_key': api_key}
        self._post_request(route, data)

    def shutdown_server(self):
        route = '/v1/shutdown/'
        self._post_request(route, None)

if __name__ == '__main__':
    remote_base = 'http://127.0.0.1:5000'
    client = Client(remote_base)

    # Create environment
    env_id = 'CartPole-v0'
    instance_id = client.env_create(env_id)

    # Check properties
    all_envs = client.env_list_all()
    action_info = client.env_action_space_info(instance_id)
    obs_info = client.env_observation_space_info(instance_id)

    # Run a single step
    client.env_monitor_start(instance_id, directory='tmp', force=True)
    init_obs = client.env_reset(instance_id)
    [observation, reward, done, info] = client.env_step(instance_id, 1, True)
    client.env_monitor_close(instance_id)
    client.upload(training_dir='tmp')

    


