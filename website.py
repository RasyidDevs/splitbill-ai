import streamlit as st
import pandas as pd
from src.vlm import SplitBillGPT
from src.prompt import split_bill_prompt

if "split_bill_gpt" not in st.session_state:
    st.session_state.split_bill_gpt = SplitBillGPT(split_bill_prompt)

if "people" not in st.session_state:
    st.session_state.people = []

if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None

if "response" not in st.session_state:
    st.session_state.response = None

if "menu_person_list" not in st.session_state:
    st.session_state.menu_person_list = {}

if "menu_quantity_left" not in st.session_state:
    st.session_state.menu_quantity_left = None

if "add_person" not in st.session_state:
    st.session_state.add_person = False
st.title("Our Split Bill 🤑")

if st.session_state.uploaded_file is None:
    uploaded_file = st.file_uploader("Insert receipt image", type=["png", "jpg", "jpeg"])
    if uploaded_file:
        st.session_state.uploaded_file = uploaded_file
        st.rerun()

if st.session_state.uploaded_file:
    st.subheader("Your Receipt:")
    col1, col2 = st.columns([1, 2])

    with col1:
        st.image(st.session_state.uploaded_file)
        back_button = st.button("Back", type="primary")
        if back_button:
            st.session_state.people = []
            st.session_state.uploaded_file = None
            st.session_state.response = None
            st.session_state.menu_person_list = {}
            st.rerun()

    with col2:
        if st.session_state.response is None:
            with st.spinner("Reading your receipt..."):
                st.session_state.response = st.session_state.split_bill_gpt.response(
                    st.session_state.uploaded_file.type,
                    st.session_state.uploaded_file
                )

        response = st.session_state.response
        data = pd.DataFrame(response["items"])

        # CEK DUPLIKAT
        if data["name"].duplicated().any():
            st.error("Ada nama barang yang duplikat")
            st.stop()

        st.dataframe(data)

        st.markdown(f"""
        <h4><b>Subtotal:</b> {response['summary']['subtotal']}</h4>
        <h4><b>Adds-on:</b> {response['summary']['adds_on']}</h4>
        <h4><b>Total:</b> {response['summary']['total']}</h4>
        """, unsafe_allow_html=True)

        if st.session_state.menu_quantity_left is None:
            st.session_state.menu_quantity_left = {
                row["name"]: row["quantity"]
                for _, row in data.iterrows()
            }
        print(st.session_state.menu_quantity_left)

    st.markdown("---")

    if st.session_state.response:
        st.subheader("Assign Bill to Your Friend!")

        new_person = st.text_input("Enter a person name:", key="person_input")
        add_clicked = st.button("Add")

        if add_clicked:
            if new_person.strip() != "" and new_person not in st.session_state.menu_person_list:
                st.session_state.people.append(new_person)
                if new_person not in st.session_state.menu_person_list:
                    st.session_state.menu_person_list[new_person] = {
                        "nums": 1,
                        "items": {row["name"]: 0 for _, row in data.iterrows()}
                    }
                st.session_state.add_person = True
                st.rerun()
            else:
                st.error("Cant use empty name or name already exist")


        for idx, person in list(enumerate(st.session_state.people)):
            with st.container(border=True):
                header_col, delete_col = st.columns([11, 1])

                with header_col:
                    st.markdown(
                        f"<h4 style='margin-top: 0.75rem; margin-bottom: 0.5rem;'>{person}</h4>",
                        unsafe_allow_html=True
                    )

                with delete_col:
                    if st.button("X", key=f"delete_person_{person}_{idx}", type="secondary"):
                        
                        if person in st.session_state.menu_person_list:
                            person_items = st.session_state.menu_person_list[person]["items"]

                            for item_name, qty in person_items.items():
                                st.session_state.menu_quantity_left[item_name] += qty

                            del st.session_state.menu_person_list[person]

                        if idx < len(st.session_state.people):
                            st.session_state.people.pop(idx)

                        st.rerun()



                nums = st.session_state.menu_person_list[person]["nums"]
                items_dict = st.session_state.menu_person_list[person]["items"]
                menu = [k for k, v in st.session_state.menu_quantity_left.items() if v > 0]


                keys = [k for k, v in items_dict.items() if v > 0]

                print(menu)
                for index in range(nums):
                    menu_col, add_button_col = st.columns([8, 2])

                    is_existing = index < len(keys)

                    if is_existing:
                        item_name = keys[index]
                        quantity = items_dict[item_name]
                        quantity_left = st.session_state.menu_quantity_left[item_name]
                        max_qty = int(data.loc[data["name"] == item_name, "quantity"].iloc[0])
                    else:
                        item_name = None

                    with menu_col:
                        if is_existing:
                            x_col, item_col, button_col = st.columns([1, 2, 3])

                            with x_col:
                                remove_item = st.button("X", key=f"remove_{person}_{item_name}", type="tertiary")
                                if remove_item:
                                    st.session_state.menu_quantity_left[item_name] += quantity
                                    del items_dict[item_name]
                                    st.session_state.menu_person_list[person]["nums"] -= 1
                                    st.rerun()

                            with item_col:
                                st.write(f"#### {item_name}")

                            with button_col:
                                col_minus, col_qty, col_plus, col_error = st.columns([1,1,1,4])

                                with col_minus:
                                    minus = st.button("−−", key=f"minus_{person}_{item_name}", type="tertiary")
                                    if minus and quantity > 1:
                                        items_dict[item_name] -= 1
                                        st.session_state.menu_quantity_left[item_name] += 1
                                        st.rerun()

                                with col_qty:
                                    st.write(f"**{quantity}**")

                                with col_plus:
                                    plus = st.button("✚", key=f"plus_{person}_{item_name}", type="tertiary")
                                    if plus:
                                        if quantity < max_qty and quantity_left > 0:
                                            items_dict[item_name] += 1
                                            st.session_state.menu_quantity_left[item_name] -= 1
                                            st.rerun()
                                        else:
                                            with col_error:
                                                st.error("Limit Reached")
                        else:
                            if sum(st.session_state.menu_quantity_left.values()) != 0:
                                select_menu = st.selectbox(
                                    "Select Menu",
                                    menu,
                                    key=f"select_menu_{person}_{index}"
                                )

                    with add_button_col:
                        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)

                        if not is_existing:
                            if sum(st.session_state.menu_quantity_left.values()) == 0:
                                with menu_col:
                                    st.success("All items are assigned! No more items left.")
                            else:
                                add_menu = st.button("✚", key=f"add_menu_{person}_{index}")
                                if add_menu:
                                    items_dict[select_menu] = 1
                                    st.session_state.menu_person_list[person]["nums"] += 1
                                    st.session_state.menu_quantity_left[select_menu] -= 1
                                    st.rerun()

        if sum(st.session_state.menu_quantity_left.values()) > 0 and st.session_state.add_person and  st.session_state.menu_person_list:
            st.warning("There's items left")
        elif sum(st.session_state.menu_quantity_left.values()) == 0 and  st.session_state.menu_person_list:
            if st.button("Submit", type="primary"):
                st.subheader("cost per person:")
                tax = response["summary"]["adds_on"]
                tax_percentage = tax / response["summary"]["subtotal"]
                for person_name, person_data in st.session_state.menu_person_list.items():
                    total_per_person = 0
                    for item_name, quantity in person_data["items"].items():
                        total_per_person += quantity * data[data["name"] == item_name]["unit_price"].values[0]
                    total_per_person += tax_percentage * total_per_person
                    st.write(f"{person_name} total items: {total_per_person}")


                        
                