import os
#
#
# def rename_folder(name_hikka, new_name):
#     """Переименовывает папку по указанному пути"""
#     folder_path = f'./Hikka/{name_hikka}'
#     print(folder_path)
#     try:
#         # Определяем родительскую директорию
#         parent_dir = os.path.dirname(folder_path)
#
#         # Формируем полный путь к новому имени папки
#         new_full_path = os.path.join(parent_dir, new_name)
#
#         # Переименовываем папку
#         os.rename(folder_path, new_full_path)
#         print(f"Папка успешно переименована в {new_name}")
#     except FileNotFoundError:
#         print("Файл или папка не найдены.")
#     except PermissionError:
#         print("Отсутствуют разрешения на переименование.")
#     except Exception as e:
#         print(f"Ошибка: {e}")


# Получаем имя пользователя
username = os.getlogin()

# Определяем корневой диск
root_disk = os.path.splitdrive(os.getcwd())[0]

# Выводим полученные значения
print(f"Пользователь: {username}")
print(f"Диск: {root_disk}")

def search_hikka():
    # Путь к директории, которую будем сканировать
    path = f'{root_disk}/Users/{username}/Desktop/MegaHost/Userbots/Hikka'

    # Имена папок, которые мы ищем
    target_folders = ['hikka 1', 'hikka 2', 'folder3']

    # Список найденных папок
    found_folders = []

    for folder_name in target_folders:
        # Полностью путь к искомой папке
        full_path = os.path.join(path, folder_name)

        if os.path.exists(full_path) and os.path.isdir(full_path):
            found_folders.append(folder_name)

    print("Найденные папки:", found_folders)

search_hikka()