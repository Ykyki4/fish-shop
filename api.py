import os
import pathlib
from urllib.parse import urlsplit, unquote

import requests


def get_access_token(client_id):
    data = {
        'client_id': client_id,
        'grant_type': 'implicit',
    }

    response = requests.post('https://api.moltin.com/oauth/access_token', data=data)

    response.raise_for_status()

    return response.json()['access_token'], response.json()['expires']


def get_products(access_token):
    headers = {
        'Authorization': f'Bearer {access_token}',
    }

    response = requests.get('https://api.moltin.com/catalog/products', headers=headers)
    response.raise_for_status()

    return response.json()['data']


def get_product_by_id(access_token, product_id):
    headers = {
        'Authorization': f'Bearer {access_token}',
    }

    response = requests.get(f'https://api.moltin.com/catalog/products/{product_id}', headers=headers)
    response.raise_for_status()

    return response.json()['data']

def download_photo(token, img_id):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }

    response = requests.get(f'https://api.moltin.com/v2/files/{img_id}', headers=headers)
    response.raise_for_status()

    img_url = response.json()['data']['link']['href']

    split_url = urlsplit(unquote(img_url))
    extension = os.path.splitext(split_url.path)[1]

    pathlib.Path('images/').mkdir(exist_ok=True)
    filename = pathlib.Path(f'images/{img_id}{extension}')
    if not filename.exists():
        response = requests.get(img_url)
        response.raise_for_status()

        with open(filename, 'wb') as file:
            file.write(response.content)

    return filename


def get_cart(access_token, cart_id):
    headers = {
        'Authorization': f'Bearer {access_token}',
    }

    response = requests.get(f"https://api.moltin.com/v2/carts/{cart_id}", headers=headers)
    response.raise_for_status()
    items_response = requests.get(f"https://api.moltin.com/v2/carts/{cart_id}/items", headers=headers)
    items_response.raise_for_status()

    return response.json()['data'], items_response.json()['data']


def add_product_to_cart(access_token, cart_id, product_id, quantity):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }

    cart_data = {
        'data': {
            "id": product_id,
            "type": "cart_item",
            "quantity": int(quantity),
        },
    }
    response = requests.post(f"https://api.moltin.com/v2/carts/{cart_id}/items", headers=headers, json=cart_data)
    response.raise_for_status()

    return response.json()


def delete_from_cart(access_token, cart_id, product_id):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }

    response = requests.delete(f"https://api.moltin.com/v2/carts/{cart_id}/items/{product_id}", headers=headers)
    response.raise_for_status()

    return response.json()


def create_customer(access_token, name, email):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }

    customer_data = {
        'data': {
            "type": "customer",
            "name": name,
            "email": email,
        },
    }

    response = requests.post(f"https://api.moltin.com/v2/customers", headers=headers, json=customer_data)
    response.raise_for_status()

    return response
