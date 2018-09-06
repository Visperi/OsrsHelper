import json


def check_new_items():
    try:
        with open("names.json") as data_file:
            data = json.load(data_file)
    except FileNotFoundError:
        input("Could not find file names.json.")
        return

    with open("Tradeables.json") as data_file2:
        tradeables = json.load(data_file2)

    new_items = []
    for id_ in data:
        if data[id_]["name"] not in tradeables:
            new_items.append("{}, {}".format(data[id_]["name"], id_))

    with open("names.json", "w") as data_file:
        json.dump(data, data_file, indent=4)

    if len(new_items) == 0:
        input("0 new items to add.")
        return
    else:
        print(f"{len(new_items)} new items:\n\n{json.dumps(new_items)}")

    user_input = input("\n\nDo you want to add the items into Tradeables.json? (y/n): ")
    if user_input == "y":
        for item in new_items:
            item = item.split(", ")
            tradeables[item[0]] = {"high_alch": "", "id": int(item[1])}
        with open("Tradeables.json", "w") as data_file:
            json.dump(tradeables, data_file, indent=4)
        print("Successfully added the items into Tradeables.json.")

    elif user_input == "n":
        input("No items will be added to the file. Closing...")


if __name__ == '__main__':
    check_new_items()
