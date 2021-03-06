import os
import json
from requests import Request, Session, codes
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

NO_CONNECTION = "Sem conexão com o servidor"

TOKEN = os.getenv('TOKEN')

KEYS = [
    os.getenv('KEY1'),
    os.getenv('KEY2'),
    os.getenv('KEY3'),
]

class Commands:
    base_url = 'http://127.0.0.1:8200'

    def create_request(self, request_type, url, data=None, headers=None, content=None):
        url = self.base_url + url
        request_type = request_type.upper()
        s = Session()
        req = Request(
            request_type,
            url,
            data=data,
            headers=headers
        )
        prepare = req.prepare()
        if content:
            prepare.body = content
        resp = s.send(prepare)
        return resp

    def is_on(self):
        # Retorna um booleano correspondente a
        # se a API está inicialidada ou não
        req = self.create_request('get', url='/v1/sys/init')
        if req.status_code == codes.ok:
            return req.json()['initialized']
        raise NO_CONNECTION

    def is_seal(self):
        if self.is_on():
            req = self.create_request('get', url='/v1/sys/seal-status')
            if req.status_code == codes.ok:
                return req.json()['sealed']
        raise NO_CONNECTION

    def unseal(self):
        if self.is_seal:
            for k in KEYS:
                data = { 'key': k }
                req = self.create_request('put', '/v1/sys/unseal', data=json.dumps(data))

    def seal(self):
        header = {'X-Vault-Token': TOKEN}
        req = self.create_request('put', url='/v1/sys/seal', headers=header)

    def create_secret(self, pk, key):
        header = {'X-Vault-Token': TOKEN, 'Content-Type': 'application/json'}
        data = {'key': key.decode('latin-1', 'replace')}
        is_seal_true = True
        while is_seal_true:
            req = self.create_request('post', url=f'/v1/secret/user/{pk}', data=json.dumps(data), headers=header)
            if req.status_code == 500:
                continue
            is_seal_true = False

    def get_secret(self, pk):
        if self.is_seal:
            self.unseal()
            header = {'X-Vault-Token': TOKEN, 'Content-Type': 'application/json'}
            is_seal_true = True
            while is_seal_true:
                req = self.create_request('get', url=f'/v1/secret/user/{pk}', headers=header)
                if req.status_code == 500:
                    continue

                if req.status_code == codes.ok:
                    is_seal_true = False
                    return req.json()['data']['key']



if __name__ == '__main__':
    c = Commands()
    c.unseal()