from database import get_db_session
from crud import store_crud


def main():
    with get_db_session() as s:
        stores = store_crud.get_all(s, limit=100)
        if not stores:
            print("No stores found in DB")
            return
        for st in stores:
            # Print key fields to inspect formats
            print(
                f"store_id={st.store_id!r}, store_name={st.store_name!r}, address={st.address!r}, phone={st.store_phone!r}")


if __name__ == '__main__':
    main()
