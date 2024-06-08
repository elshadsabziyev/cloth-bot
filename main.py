import time
import streamlit as st
from auth import FirebaseAuthenticator
from realtimedb import RealtimeDB
import pandas as pd
import datetime
from datetime import timedelta as tdlt
from datetime import datetime as dt
from typing import List
from together import Together
from credential_loader import Credentials
from streamlit import components


class ChatBot:
    def __init__(self, api_key):
        self.client = Together(api_key=api_key)
        if "messages" not in st.session_state:
            # Load products from CSV
            products_df = pd.read_csv("assets/your_data.csv")
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
        return f"#### {self.name} (${self.price})\n **{self.category}**"


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


class App(FirebaseAuthenticator, RealtimeDB):
    def __init__(self):
        super().__init__()
        self.set_page_config()

    def set_page_config(self):
        st.set_page_config(
            page_title="Farm Dashboard",
            page_icon="🏬",
            layout="wide",
            initial_sidebar_state="auto",
        )

    def auth_page(self):
        if "user_info" not in st.session_state:
            col1, col2, col3 = st.columns([2, 5, 2])
            login_register = col2.toggle(
                label="**Login/Register**", key="login_register"
            )
            if login_register:
                do_you_have_an_account = "No"
            else:
                do_you_have_an_account = "Yes"
            auth_form = col2.form(key="Authentication form", clear_on_submit=False)
            email = auth_form.text_input(
                label="**Email**",
                type="default",
                placeholder="Enter your email",
                autocomplete="email",
            )
            password = (
                auth_form.text_input(
                    label="**Password**",
                    type="password",
                    placeholder="Enter your password",
                    autocomplete="current-password",
                )
                if do_you_have_an_account in {"Yes", "No"}
                else auth_form.empty()
            )
            auth_notification = col2.empty()

            if do_you_have_an_account == "Yes":
                if auth_form.form_submit_button(
                    label="Sign In", use_container_width=True, type="primary"
                ):
                    with auth_notification, st.spinner("Signing in"):
                        self.sign_in(email, password)

                if auth_form.form_submit_button(
                    label="Forgot Password", use_container_width=True, type="secondary"
                ):
                    with auth_notification, st.spinner("Sending password reset link"):
                        self.reset_password(email)

            elif do_you_have_an_account == "No" and auth_form.form_submit_button(
                label="Create Account", use_container_width=True, type="primary"
            ):
                with auth_notification, st.spinner("Creating account"):
                    self.create_account(email, password)

            if "auth_success" in st.session_state:
                auth_notification.success(st.session_state.auth_success)
                del st.session_state.auth_success
            elif "auth_warning" in st.session_state:
                auth_notification.error(st.session_state.auth_warning)
                del st.session_state.auth_warning
        else:
            self.home_page()

    def home_page(self):
        self.sidebar()
        try:
            st.title(
                f"**Welcome, _{st.session_state.user_info['fullUserInfo']['users'][0]['email'].split('@')[0]}_!**"
            )
        except:
            st.title("**Welcome!**")
        st.info(
            """
            # KalagAI
            """
        )

        # Load products from CSV
        catalog = ProductCatalog("assets/your_data.csv")
        products = catalog.get_products()
        # Initialize the chatbot
        chatbot = ChatBot(Credentials().openai_credentials)

        # Initialize the cart
        if "cart" not in st.session_state:
            st.session_state.cart = Cart()

        # Display products
        with st.status(label="**Loading products...**", expanded=False) as status_0:
            st.write("## Products")
            cols = st.columns(3)
            for i, product in enumerate(products):
                with cols[i % 3]:
                    with st.container(border=True, height=500):
                        st.write(str(product))
                        with st.container(border=True, height=280):
                            st.image(product.photo, use_column_width=True)
                        add_button = st.button("Add to Cart", key=f"add_{i}")
                        if add_button:
                            st.session_state.cart.add_item(product)
                            st.toast(f"**{product.name} added to cart!**", icon="🛒")
            status_0.update(label="**Products loaded!**", state="complete", expanded=True)
                    
        for message in st.session_state["messages"]:
            if message["role"] != "system":  # Skip system messages
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        if prompt := st.chat_input("Ask me anything!"):
 
        #     st.markdown(
        #             f"""
        # <script>
        #     window.scrollTo({{
        #         top: document.body.scrollHeight,
        #         behavior: 'smooth' // Optional: Add smooth scrolling effect
        #     }});
        # </script>
        # """,
        #             unsafe_allow_html=True,
        #         )
            st.session_state["messages"].append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                status_0.update(label="**Minimized! - Expand to view products**", state="complete", expanded=False)
                st.markdown(prompt)

            with st.status(label="**We are cooking up a response...**", expanded=False) as status:
                with st.chat_message("assistant"):
                    message_placeholder = st.empty()
                    full_response = chatbot.ask(prompt)
                    message_placeholder.markdown(full_response + "▌")
                st.session_state["messages"].append(
                    {"role": "assistant", "content": full_response}
                )
                status.update(label="**Response is ready!**", state="complete", expanded=True)
        cols = st.columns([20, 10, 20])
        with cols[0]:
            st.empty()
        with cols[1]:
            if len(st.session_state.get("messages", [])) > 1:
                if st.button("Clear Chat", use_container_width=True):
                    chatbot.clear_chat()
                    status_0.update(label="**Chat cleared!**", state="complete", expanded=True)
                    st.rerun()
        with cols[2]:
            st.empty()

    def sidebar(self):
        st.sidebar.write("# Your Account")

        if st.sidebar.button("**Sign Out**"):
            session_state_variables = [
                "user_info",
                "delete_account_warning_shown",
                "delete_account_clicked",
                "auth_success",
                "auth_warning",
                "auth_error",
                "messages",
                "cart",
            ]

            for var in session_state_variables:
                try:
                    del st.session_state[var]
                except KeyError:
                    continue
            st.sidebar.success(
                """
                    ##### Signed out successfully.
                    - You have been signed out.
                    - Sign in to access your account.
                    """
            )
            time.sleep(2)
            st.rerun()
        with st.sidebar.expander("**Premium Access**"):
            st.write(
                f"**Email:** {st.session_state.user_info['fullUserInfo']['users'][0]['email']}"
            )
            st.write(f"""### Your account has premium access, this includes:""")
            st.write(
                """ 
                - Chat with the AI assistant.\n
                - Premnium Support.\n
                **More features coming soon!**
                """
            )
        with st.sidebar.expander("**Click for Account Settings**"):
            self.account_settings()

        # Initialize the cart if it doesn't exist
        if "cart" not in st.session_state:
            st.session_state.cart = Cart()

        cart_expander = st.sidebar.expander(
            f"**Show Cart [{len(st.session_state.cart.items)} items]**"
        )
        with cart_expander:
            if not st.session_state.cart.items:
                st.write("Your cart is empty.")
            else:
                for item in st.session_state.cart.items:
                    st.write(str(item))
                total = st.session_state.cart.get_total()
                st.write(f"Total: ${total:.2f}")
            cols = st.columns([1, 20, 20, 20, 1])
            with cols[0]:
                st.empty()
            with cols[1]:
                if st.button("Checkout", help="Proceed to checkout"):
                    st.toast("Checkout feature coming soon!", icon="✅")
            with cols[2]:
                if st.button("Clear Cart", help="Remove all items from the cart"):
                    st.session_state.cart.empty_cart()
            with cols[3]:
                st.button("Refresh Cart", key="refresh_cart")
            with cols[4]:
                st.empty()
        st.sidebar.info(
            """
            # About
            - Made with ❤️ by [KalagAI](https://kalagai.streamlit.app) team.
            """
        )

    def account_settings(self):
        with st.form(key="delete_account_form", clear_on_submit=True):
            st.subheader("Delete Account:")
            password = st.text_input("**Enter your password**", type="password")
            submit_button = st.form_submit_button(label="**Confirm Delete Account**")
            if submit_button:
                if st.session_state.get("delete_account_warning_shown", False):
                    # Verify the password again before deleting the account
                    if self.verify_password(password):
                        with st.spinner("Deleting account"):
                            self.delete_account(password)
                        if "auth_success" in st.session_state:
                            st.success(st.session_state.auth_success)
                            del st.session_state.auth_success
                            time.sleep(2)
                            st.rerun()
                        elif "auth_warning" in st.session_state:
                            st.error(st.session_state.auth_warning)
                            del st.session_state.auth_warning
                        st.session_state.delete_account_clicked = False
                        st.session_state.delete_account_warning_shown = False
                    else:
                        st.error(
                            """Incorrect password, or too many attempts. Please try again."""
                        )
                else:
                    # Verify the password when the user first enters it
                    if self.verify_password(password):
                        st.warning(
                            "Are you sure you want to delete your account? This action cannot be undone! If you are sure, please retype your password and click the button again."
                        )
                        st.session_state.delete_account_warning_shown = True
                    else:
                        st.error("Incorrect password. Please try again.")
        with st.form(key="Reset", clear_on_submit=True):
            st.subheader("Reset Password:")
            st.info(
                "After clicking the button below, a password reset link will be sent to your email address."
            )
            submit_button = st.form_submit_button(label="**Reset Password**")
            if submit_button:
                with st.spinner("Resetting password"):
                    self.reset_password(
                        st.session_state.user_info["fullUserInfo"]["users"][0]["email"]
                    )
                if "auth_success" in st.session_state:
                    st.success(st.session_state.auth_success)
                    del st.session_state.auth_success
                elif "auth_warning" in st.session_state:
                    st.error(st.session_state.auth_warning)
                    del st.session_state.auth_warning


if __name__ == "__main__":
    app = App()
    app.auth_page()
