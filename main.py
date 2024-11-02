import bfs
import dfs
import a_start
import ucs

def menu():
    print("Chọn chương trình để chạy:")
    print("1. Chạy bfs")
    print("2. Chạy dfs")
    print("3. Chạy A*")
    print("4. Chạy ucs")
    print("0. Thoát")
    return input("Nhập lựa chọn của bạn: ")

while True:
    choice = menu()
    if choice == "1":
        bfs.main()
    elif choice == "2":
        dfs.main()
    elif choice == "3":
        a_start.main()
    elif choice == "4":
        ucs.main()
    elif choice == "0":
        print("Thoát chương trình.")
        break
    else:
        print("Lựa chọn không hợp lệ. Vui lòng chọn lại.")
