import requests
import json
from tqdm import tqdm

class User:
    def __init__(self, vk_id, vk_token, yandex_disc_token):
        self.vk_id = vk_id
        self.vk_token = vk_token
        self.yandex_disc_token = yandex_disc_token
        self.BASE_YANDEX_HEADERS = {'Authorization': 'OAuth ' + self.yandex_disc_token}

    def get_vk_request(self, method_name, add_params: dict):
        params = {'access_token': self.vk_token,
                  'v': '5.126'
                  }
        if add_params:
            params.update(add_params)
        result = requests.get(f'{BASE_VK_URL}/{method_name}', params=params)
        self._check_response(result)
        return result.json()

    def get_vk_user_id(self):
        vk_user_params = {'user_ids': self.vk_id}
        result = self.get_vk_request('/users.get', vk_user_params)
        return result['response']

    def get_vk_photo(self, album_id='profile', photos_count=5):
        vk_id = self.get_vk_user_id()
        if album_id != 'profile':
            albums = self.get_vk_albums(vk_id)
            albums = [{'id': album['id'], 'title': album['title']} for album in albums]
            if album_id not in [album['id'] for album in albums]:
                raise Exception('неверный id альбома')

        get_photo_params = {'owner_id': vk_id,
                            'album_id': album_id,
                            'extended': 1,
                            'count': photos_count
                            }
        result = self.get_vk_request('/photos.get', get_photo_params)
        photos = result['response']['items']
        return photos

    def get_vk_albums(self, vk_id):
        get_albums_params = {'owner_id': vk_id, 'need_system': True}
        result = self.get_vk_request('/photos.getAlbums', get_albums_params)
        albums = result['response'][0]['items']
        return albums

    def get_photo_by_size(self, photos, size='z'):
        photos = [photo['sizes'] for photo in photos]
        photo_by_size = []
        for photo in photos:
            for sizes in photo:
                if sizes['type'] == size:
                    photo_by_size.append({'size': sizes['type'], 'url': sizes['url']})
        return photo_by_size

    def get_photo_name(self, photos):
        likes_and_dates = [{'likes': photo['likes']['count'], 'date': photo['date']} for photo in photos]
        file_names = []
        for element in likes_and_dates:
            name = str(element['likes']) + '.jpg'
            if name in file_names:
                name = str(element['date']) + name
            file_names.append(name)
        return file_names

    def create_folder(self, folder_name='vk_photo'):
        params = {'path': folder_name}
        url = BASE_YANDEX_URL + '/resources'
        result = requests.put(url, headers=self.BASE_YANDEX_HEADERS, params=params)
        self._check_response(result)
        return folder_name

    def upload_to_yandex_disc(self):
        folder_name = self.create_folder()
        vk_photos = self.get_vk_photo()
        names = self.get_photo_name(vk_photos)
        photos = self.get_photo_by_size(vk_photos)
        photo_url = [photo['url'] for photo in photos]
        photo_size = [photo['size'] for photo in photos]
        url = BASE_YANDEX_URL + '/resources/upload'
        log = []
        for name, photo_url, size in tqdm(list(zip(names, photo_url, photo_size))):
            params = {'path': f'/{folder_name}/{name}', 'url': photo_url}
            result = requests.post(url, headers=self.BASE_YANDEX_HEADERS, params=params)
            self._check_response(result)
            log.append({'file_name': name, 'size': size})
        result = self.write_json_log(log)
        return result

    def write_json_log(self, log):
        with open('logs.json', 'a') as write_file:
            json.dump(log, write_file)
        return log

    def _check_response(self, req):
        if not req.ok:
            if req.status_code == 409:
                return
            else:
                raise Exception(req.status_code, req.text)


if __name__ == '__main__':
    BASE_YANDEX_URL = 'https://cloud-api.yandex.net/v1/disk'
    BASE_VK_URL = 'https://api.vk.com/method'
    VK_ACCESS_TOKEN = input('Введите ваш ВК ТОКЕН: ')
    YANDEX_DISC_OAUTH = input('Теперь введите ваш Яндекс ТОКЕН: ')
    VK_User = User('', VK_ACCESS_TOKEN, YANDEX_DISC_OAUTH)
    print(VK_User.upload_to_yandex_disc())