import file_sweeper
import os
import requests

class qBittorrentClientManager:
    def __init__(self, ip=os.getenv("TR_IP"), port=os.getenv("TR_PORT"), 
                 username=os.getenv("TR_USERNAME"), password=os.getenv("TR_PASSWORD")):

        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.login()

    def login(self):
        url = f"http://{self.ip}:{self.port}/api/v2/auth/login"
        data = {
            "username": self.username,
            "password": self.password
        }
        response = self.session.post(url, data=data)
        if response.text != "Ok.":
            raise Exception("Failed to log in to qBittorrent")

    def get_torrents_list(self):
        url = f"http://{self.ip}:{self.port}/api/v2/torrents/info"
        response = self.session.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return []

    def delete_torrent_and_data(self, torrent_ids):
        url = f"http://{self.ip}:{self.port}/api/v2/torrents/delete"
        data = {
            "hashes": "|".join(torrent_ids),
            "deleteFiles": True
        }
        response = self.session.post(url, data=data)
        return response.status_code == 200

    @staticmethod
    def check_torrents_existence(rpc_list, my_list, root_dir):
        """
        Checks if all elements of torrents_list are present in the list of torrents returned by get_torrents_list(client).

        Args:
            torrents_list (list): List of torrents to check.
            root_dir (str): Root directory to be removed from the paths in torrents_list.

        Returns:
            bool: True if all elements are present, False otherwise.
        """

        # Extract torrent names from the qBitTorrent list
        torrent_names = [torrent['name'] for torrent in rpc_list]

        # Extract torrent names from file_sweeper.main list by deleting root_dir
        cleaned_torrents = [path.replace(root_dir+'/', '') for path in my_list]

        # Checks whether all the elements in cleaned_torrents are present in torrent_names
        return all(torrent_name in torrent_names for torrent_name in cleaned_torrents)

    def main(self, root_dir, extensions):
        """
        Main function to call other functions and return the final list.

        Args:
            root_dir (str): Root directory.
            extensions (list): List of file extensions.

        Returns:
            list: Final list of elements from my_list with their IDs if check_torrents_existence is True.
        """

        rpc_list = self.get_torrents_list()
        
        my_list = file_sweeper.main(root_dir, extensions)

        print("Completed downloads: ",len(my_list))
        # for item in my_list:
        #     print(item)

        final_list = []

        if self.check_torrents_existence(rpc_list, my_list, root_dir):
            for torrent in rpc_list:
                torrent_name = torrent['name'].replace(root_dir+'/', '')
                #print(torrent_name)
                if any(item.endswith(torrent_name) for item in my_list):
                    final_list.append((torrent['hash'], torrent['name']))

        print("Final list count: ",len(final_list))
        return final_list
##############################
if __name__ == "__main__":
    ip = "localhost"
    port = 8080
    username = "admin"
    password = "admin"
    root_dir = "./tests/data/complete" # for file_sweeper
    extensions = [".mkv", ".avi", ".mp4"] # for file_sweeper

    # to try without the docker removarr
    # you need to source your .env file
    # commands
    # $ set -a
    # $ source .env
    # $ set +a
    # python3 app.py

    tr_manager = qBittorrentClientManager()

    print(" --- debug ","-"*10,"\n")
    torrents = tr_manager.get_torrents_list()
    #print("full list:",torrents)
    torrents_info = [(torrent['hash'], torrent['name']) for torrent in torrents]
    print("list of torrents via RPC :")
    print(torrents_info)
    print()
    to_remove = file_sweeper.main(root_dir,extensions)
    print("List of torrents (folders) via final script :")
    print(to_remove)
    print()
    check_existence = tr_manager.check_torrents_existence(torrents, to_remove, root_dir)
    print("Check if all elements from file_sweeper.main are in rpc list:",check_existence)
    print()
    result = tr_manager.main(root_dir, extensions)
    print("final result:", result)
    print("-"*10)


