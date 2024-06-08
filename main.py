import streamlit as st
import pandas as pd
from typing import List
from together import Together

OEA_API_KEY = st.secrets["openai_api_key"]


class ChatBot:
    def __init__(self, api_key):
        self.client = Together(api_key=api_key)
        if "messages" not in st.session_state:
            # Load products from CSV
            products_df = pd.read_csv("your_data.csv")
            products_str = products_df.to_string(index=False)

            st.session_state["messages"] = [
                {
                    "role": "system",
                    "content": f"""Hello!  I'm your friendly style assistant, here to help you navigate our online store.  Tell me what kind of look you're going for, and I can recommend some amazing items we have in stock!  Plus, I can answer any questions you might have about styles, sizes, or anything else fashion-related.
                                    I have the following products in stock:
                                    {products_str}
                                    I will both suggest clothes in or out of stock. But i will indicate in parenthesis if the item is out of stock. Or when in stock, i will indicate the price and other information about the item in parenthesis.
                                """,
                }
            ]

    def ask(self, question):
        st.session_state["messages"].append({"role": "user", "content": question})
        response = self.client.chat.completions.create(
            model="mistralai/Mistral-7B-Instruct-v0.3",
            messages=st.session_state["messages"],
        )
        st.session_state["messages"].append(
            {"role": "assistant", "content": response.choices[0].message.content}
        )
        return response.choices[0].message.content

    def clear_chat(self):
        st.session_state["messages"] = [
            {
                "role": "system",
                "content": """Hello! I'm your AI-powered fashion assistant. I can help you find the perfect outfit, recommend items based on your preferences, and answer any questions you have about our products. I can also provide information about sizes, styles, and current fashion trends. Let's get started!""",
            }
        ]


class Product:
    def __init__(self, name, price, photo, category):
        self.name = name
        self.price = price
        self.photo = photo
        self.category = category

    def __str__(self):
        return f"{self.name} (${self.price}) - {self.category}"


class Cart:
    def __init__(self):
        self.items = []

    def add_item(self, product):
        self.items.append(product)

    def remove_item(self, product):
        self.items.remove(product)

    def empty_cart(self):
        self.items = []

    def get_total(self):
        total = 0
        for item in self.items:
            total += item.price
        return total


class ProductCatalog:
    def __init__(self, csv_file):
        self.products = self.load_products(csv_file)

    def load_products(self, csv_file) -> List[Product]:
        df = pd.read_csv(csv_file)
        products = []
        for _, row in df.iterrows():
            product = Product(
                row["Product"], row["Price"], row["Photo"], row["Category"]
            )
            products.append(product)
        return products

    def get_products(self):
        return self.products


def main():
    st.title("KalagAI")

    hide_img_fs = """
    <style>
    button[title="View fullscreen"]{
        visibility: hidden;}a
    </style>
    """
    st.markdown(hide_img_fs, unsafe_allow_html=True)

    # Load products from CSV
    catalog = ProductCatalog("your_data.csv")
    products = catalog.get_products()

    # Initialize the chatbot
    chatbot = ChatBot(OEA_API_KEY)

    # Chatbot
    st.subheader("Chatbot")
    for message in st.session_state["messages"]:
        if message["role"] != "system":  # Skip system messages
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    if prompt := st.chat_input("Ask me anything!"):
        st.session_state["messages"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("We are cooking up some recommendations for you..."):
            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = chatbot.ask(prompt)
                message_placeholder.markdown(full_response + "▌")
            st.session_state["messages"].append(
                {"role": "assistant", "content": full_response}
            )

    if st.button("Clear Chat"):
        chatbot.clear_chat()

    # Initialize the cart
    if "cart" not in st.session_state:
        st.session_state.cart = Cart()

    # Display products
    st.subheader("Products")
    cols = st.columns(3)
    for i, product in enumerate(products):
        with cols[i % 3]:
            st.write(str(product))
            with st.container(border=True, height=250):
                st.image(product.photo, use_column_width=True)
            add_button = st.button("Add to Cart", key=f"add_{i}")
            if add_button:
                st.session_state.cart.add_item(product)
                st.success(f"{product.name} added to cart!")

    # Display cart in the sidebar
    st.sidebar.subheader("Cart")
    cart_expander = st.sidebar.expander("Show Cart")
    with cart_expander:
        if not st.session_state.cart.items:
            st.write("Your cart is empty.")
        else:
            for item in st.session_state.cart.items:
                st.write(str(item))
            total = st.session_state.cart.get_total()
            st.write(f"Total: ${total:.2f}")
        if st.button("Clear Cart", help="Remove all items from the cart"):
            st.session_state.cart.empty_cart()
        # Checkout button
        if st.button("Proceed to Checkout", help="Complete your purchase"):
            if not st.session_state.cart.items:
                st.warning("Your cart is empty!")
            else:
                st.success("Checkout successful! Thank you for your purchase.")
                st.session_state.cart = Cart()  # Clear the cart after checkout


if __name__ == "__main__":
    main()
