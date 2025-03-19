import streamlit as st
import requests
import base64
import html
from PIL import Image
import io

# ---- Adjust BASE_URL ----
BASE_URL = "backend-library-production-f4c2.up.railway.app"  # Replace with your backend URL

# ---- Custom CSS ----
st.markdown("""
<style>
/* Background Image */
.stApp {
    background-image: url("https://www.istockphoto.com/fi/valokuva/rotunda-stockholmin-yleisen-kirjaston-sis%C3%A4ll%C3%A4-gm1800441007-548462204");
    background-size: cover;
    background-attachment: fixed;
    background-color: transparent !important;
}

/* Dark Theme */
[data-theme="dark"] .stApp {
    background-color: black !important;
    color: #ffffff !important;
}

/* Light Theme */
[data-theme="light"] .stApp {
    background: white !important;
    color: #000000 !important;
}

/* Card Styles */
.book-card {
    border: 1px solid #ddd;
    border-radius: 10px;
    padding: 15px;
    margin: 10px;
    height: 400px;
    overflow: hidden;
    background-color: white;
    color:black;
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    transition: transform 0.2s, box-shadow 0.2s;
}
.book-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
}
.card-image {
    height: 200px;
    width: 100%;
    object-fit: cover;
    border-radius: 8px;
}
.card-title {
    font-size: 18px;
    font-weight: bold;
    margin: 10px 0;
}
.card-author {
    font-size: 14px;
    color: #555;
    margin: 5px 0;
}
.card-actions {
    display: flex;
    justify-content: space-between;
    margin-top: 10px;
}
.card-actions button {
    background-color: #4CAF50;
    color: white;
    border: none;
    border-radius: 5px;
    padding: 5px 10px;
    cursor: pointer;
    transition: background-color 0.2s;
}
.card-actions button:hover {
    background-color: #45a049;
}
</style>
""", unsafe_allow_html=True)

# ---- Session State Initialization ----
if "wishlist" not in st.session_state:
    st.session_state.wishlist = []
if "ratings" not in st.session_state:
    st.session_state.ratings = {}

# ---- Sign Up UI ----
def signup_ui():
    st.title("🔒 Sign Up")
    new_email = st.text_input("Email Address")
    new_username = st.text_input("Choose a Username")
    new_password = st.text_input("Choose a Password", type="password")

    if st.button("Sign Up"):
        if not new_email or not new_username or not new_password:
            st.warning("⚠️ All fields are required!")
            return
        
        try:
            response = requests.post(f"{BASE_URL}/signup", json={
                "email": new_email,
                "username": new_username,
                "password": new_password
            })
            if response.status_code == 200:
                st.success("✅ Account created successfully. Please log in.")
                st.session_state["show_login"] = True
            else:
                st.error(response.json().get("detail", "Error signing up."))
        except requests.exceptions.RequestException:
            st.error("⚠️ Unable to connect to the server.")

# ---- Login UI ----
def login_ui():
    st.title("🔑 Login to Your Library")
    login_input = st.text_input("Email or Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if not login_input or not password:
            st.warning("⚠️ Please enter both username/email and password!")
            return

        payload = {"password": password}
        if "@" in login_input:
            payload["email"] = login_input
        else:
            payload["username"] = login_input

        try:
            response = requests.post(f"{BASE_URL}/login", json=payload)
            if response.status_code == 200:
                st.session_state["logged_in"] = True
                st.session_state["username"] = login_input
                st.rerun()
            else:
                st.error(response.json().get("detail", "❌ Invalid credentials!"))
        except requests.exceptions.RequestException:
            st.error("⚠️ Unable to connect to the server.")

# ---- Book Card UI ----
def book_card(book):
    with st.container():
        # Escape special characters
        title = html.escape(book.get('title', 'Unknown'))
        author = html.escape(book.get('author', 'Unknown'))
        thumbnail = book.get('thumbnail', 'https://via.placeholder.com/150')
        
        # Display book card
        st.markdown(f"""
        <div class="book-card">
            <img class="card-image" src="{base64.b64decode(thumbnail) if thumbnail else 'https://via.placeholder.com/150'}" alt="{title}">
            <div class="card-title">{title}</div>
            <div class="card-author">By {author}</div>
            <div class="card-actions">
                <button onclick="st.session_state.show_details='{title}'">View Details</button>
                <button onclick="add_to_wishlist('{title}')">❤️ Wishlist</button>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Rating
        show_rating(title)

        # Details Modal
        if st.session_state.get('show_details') == title:
            with st.expander("Book Details", expanded=True):
                st.write(f"**Year:** {book.get('year', 'N/A')}")
                st.write(f"**Genre:** {book.get('genre', 'N/A')}")
                st.write(f"**Status:** {'Read ✅' if book.get('is_read') else 'Unread ⏳'}")
                if st.button("Close", key=f"close_{title}"):
                    del st.session_state.show_details

# ---- Rating System ----
def show_rating(book_title):
    current_rating = st.session_state.ratings.get(book_title, 0)
    options = [1, 2, 3, 4, 5]
    new_rating = st.select_slider(
        "Rate this book",
        options=options,
        value=current_rating if current_rating in options else 1,
        key=f"rate_{book_title}"
    )
    if new_rating != current_rating:
        st.session_state.ratings[book_title] = new_rating
        st.success(f"Rated {book_title}: {new_rating} ★")


def get_wishlist():
    if "username" not in st.session_state:
        return []
    try:
        response = requests.get(f"{BASE_URL}/wishlist/{st.session_state['username']}")
        if response.status_code == 200:
            return response.json().get("wishlist", [])
        else:
            st.error(f"❌ Failed to fetch wishlist. Status Code: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        st.error(f"⚠️ Unable to connect to the server. Error: {e}")
        return []

# ---- Recommendations Section ----
def show_recommendations():
    st.header("📚 Book Recommendations")
    
    # Recommendation Types
    with st.expander("Recommendation Settings"):
        col1, col2 = st.columns(2)
        with col1:
            st.checkbox("Based on my favorite genres", True)
        with col2:
            st.checkbox("Surprise me!", True)
    
    # Suggested Genres
    st.subheader("Genres to Explore")
    st.write("""
    - Education
    - Mystery
    - Historical Fiction
    """)
    
    # Next to Read
    st.subheader("Next Book to Read")
    st.info("The Catcher in the Rye by J.D. Salinger")

# ---- Analytics Dashboard ----
def show_analytics():
    st.header("📊 Library Analytics")
    
    cols = st.columns(3)
    with cols[0]:
        st.metric("Total Books", 23)
    with cols[1]:
        st.metric("Read", 7)
    with cols[2]:
        st.metric("Wishlist", len(get_wishlist()))
    
    # Rating Distribution
    st.subheader("Rating Distribution")
    st.bar_chart({
        '5 ★': 12,
        '4 ★': 8,
        '3 ★': 5,
        '2 ★': 2,
        '1 ★': 1
    })
    
    # Reading Progress
    st.subheader("Reading Status")
    st.progress(0.3)
    st.write("30.4% Completed")

# ---- Import/Export Feature ----
def data_management():
    st.header("📥📤 Import/Export Data")
    
    with st.expander("Export Library"):
        st.radio("Export Format", ["CSV", "JSON"])
        st.checkbox("Include all metadata")
        if st.button("Export Now"):
            # Generate dummy file
            st.success("Export started! Your file will download shortly.")
    
    with st.expander("Import Library"):
        uploaded_file = st.file_uploader("Choose file")
        if uploaded_file:
            st.success("File uploaded successfully!")

# ---- Add Book UI ----
def add_book_ui():
    st.write("### ➕ Add a Book")
    new_title = st.text_input("Book Title")
    new_author = st.text_input("Author Name")
    new_year = st.text_input("Publication Year")
    new_genre = st.text_input("Genre")
    new_thumbnail = st.file_uploader("Thumbnail", type=["jpg", "jpeg", "png"])
    is_read = st.checkbox("Mark as Read")

    if st.button("Add Book 📚"):
        if not new_title or not new_author:
            st.warning("⚠️ Title and Author are required!")
        else:
            thumbnail_data = None
            if new_thumbnail:
                thumbnail_data = base64.b64encode(new_thumbnail.read()).decode()
            
            try:
                response = requests.post(f"{BASE_URL}/books", json={
                    "title": new_title,
                    "author": new_author,
                    "year": new_year,
                    "genre": new_genre,
                    "thumbnail": thumbnail_data,
                    "is_read": is_read
                })
                if response.status_code == 200:
                    st.success(f"✅ '{new_title}' added to the bookshelf!")
                else:
                    st.error("❌ Failed to add book.")
            except requests.exceptions.RequestException:
                st.error("⚠️ Unable to connect to the server.")

# ---- Remove Book UI ----
def remove_book_ui():
    st.write("### 🗑️ Remove a Book")
    book_title = st.text_input("Enter Book Title to Remove")

    if st.button("Remove Book"):
        try:
            response = requests.delete(f"{BASE_URL}/books/{book_title}")
            if response.status_code == 200:
                st.success("✅ Book removed successfully!")
            else:
                st.error("❌ Failed to remove book.")
        except requests.exceptions.RequestException:
            st.error("⚠️ Unable to connect to the server.")

# ---- Update Book UI ----
def update_book_ui():
    st.write("### ✏️ Update a Book")
    book_title = st.text_input("Enter Book Title to Update")
    new_title = st.text_input("New Title")
    new_author = st.text_input("New Author")
    new_year = st.text_input("New Publication Year")
    new_genre = st.text_input("New Genre")
    new_thumbnail = st.file_uploader("New Thumbnail", type=["jpg", "jpeg", "png"])
    is_read = st.checkbox("Mark as Read")

    if st.button("Update Book"):
        thumbnail_data = None
        if new_thumbnail:
            thumbnail_data = base64.b64encode(new_thumbnail.read()).decode()
        
        try:
            response = requests.put(f"{BASE_URL}/books/{book_title}", json={
                "title": new_title,
                "author": new_author,
                "year": new_year,
                "genre": new_genre,
                "thumbnail": thumbnail_data,
                "is_read": is_read
            })
            if response.status_code == 200:
                st.success("✅ Book updated successfully!")
            else:
                st.error("❌ Failed to update book.")
        except requests.exceptions.RequestException:
            st.error("⚠️ Unable to connect to the server.")

# ---- Search Book UI ----
def add_to_wishlist(book_title):
    """ Adds a book to the user's wishlist """
    if "username" not in st.session_state and "email" not in st.session_state:
        st.warning("⚠️ Please log in to add to wishlist!")
        return

    try:
        payload = {
            "book_title": book_title,
            "username": st.session_state.get("username", ""),
            "email": st.session_state.get("email", ""),
        }
        response = requests.post(f"{BASE_URL}/wishlist", json=payload)
        response.raise_for_status()  # Raise an error for bad status codes
        st.success(f"✅ '{book_title}' added to wishlist!")
    except requests.exceptions.HTTPError as e:
        st.error(f"❌ HTTP Error: {e}")
    except requests.exceptions.RequestException as e:
        st.error(f"⚠️ Unable to connect to the server. Error: {e}")

# ---- Search Book UI ----
def search_book_ui():
    st.write("### 🔍 Search for a Book")
    search_query = st.text_input("Enter Book Title or Author")

    if st.button("Search"):
        try:
            # Search in Google Books API
            google_books_url = f"https://www.googleapis.com/books/v1/volumes?q={search_query}"
            google_response = requests.get(google_books_url)
            google_books = google_response.json().get("items", [])

            # Search in local database
            local_response = requests.get(f"{BASE_URL}/books/search", params={"query": search_query})
            local_books = local_response.json() if local_response.status_code == 200 else []

            # Combine results
            combined_books = []

            # Process Google Books data
            for book in google_books:
                volume_info = book.get("volumeInfo", {})
                combined_books.append({
                    "title": html.escape(volume_info.get("title", "Unknown")),
                    "author": html.escape(", ".join(volume_info.get("authors", ["Unknown"]))),
                    "thumbnail": volume_info.get("imageLinks", {}).get("thumbnail", "https://via.placeholder.com/150"),
                    "source": "Google Books",
                    "description": html.escape(volume_info.get("description", "No description available."))
                })

            # Process local database books
            for book in local_books:
                thumbnail = book.get("thumbnail", "")

                if thumbnail:
                    try:
                        # Decode Base64 string to bytes
                        thumbnail_bytes = base64.b64decode(thumbnail)

                        # Convert bytes to PIL Image
                        image = Image.open(io.BytesIO(thumbnail_bytes))

                        # Display image in Streamlit
                        st.image(image, width=150, caption=book["title"])
                        if image.mode == "RGBA":
                            image = image.convert("RGB")  
                        # Save image to a temporary file
                        image.save("temp_thumbnail.jpg")
                        thumbnail = "temp_thumbnail.jpg"

                    except Exception as e:
                        st.error(f"⚠️ Failed to decode thumbnail: {e}")
                        thumbnail = "https://via.placeholder.com/150"
                else:
                    thumbnail = "https://via.placeholder.com/150"

                combined_books.append({
                    "title": html.escape(book.get("title", "Unknown")),
                    "author": html.escape(book.get("author", "Unknown")),
                    "thumbnail": thumbnail,
                    "source": "Local Database",
                    "description": html.escape(book.get("description", "No description available."))
                })

            # Store combined_books in session state
            st.session_state["combined_books"] = combined_books

        except requests.exceptions.RequestException:
            st.error("⚠️ Unable to connect to the server.")

    # Display Search Results
    if "combined_books" in st.session_state:
        combined_books = st.session_state["combined_books"]
        if combined_books:
            st.write("### Search Results")
            cols = st.columns(3)  # Grid layout with 3 columns
            
            for i, book in enumerate(combined_books):
                with cols[i % 3]:
                    st.markdown(f"""
                    <div class="book-card">
                        <img class="card-image" src="{book['thumbnail']}" alt="{book['title']}">
                        <div class="card-title">{book['title']}</div>
                        <div class="card-author">By {book['author']}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Use st.form to prevent page reload
                    with st.form(key=f"form_{i}"):
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            if st.form_submit_button(f"🔍 View"):
                                st.session_state["selected_book"] = book  # Store selected book in session state
                        with col2:
                            if st.form_submit_button(f"Wishlist"):
                                add_to_wishlist(book["title"])

            # Add styling for buttons (Flexbox)
            st.markdown("""
            <style>
                .book-card {
                    background:#DDA0DD;
                    padding: 15px;
                    border-radius: 10px;
                    text-align: center;
                    box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
                    margin-bottom: 15px;
                    min-height: 250px;
                }
                .card-image {
                    max-width: 180px;
                    height: 180px;
                    margin-bottom: 10px;
                }
                .card-title {
                    font-weight: bold;
                    font-size: 16px;
                }
                .card-author {
                    font-size: 14px;
                    color: #000000;
                    margin-bottom: 10px;
                }
            </style>
            """, unsafe_allow_html=True)
        else:
            st.warning("📖 No books found in Google Books or local database.")

    # ✅ Full Book Details Modal
    if "selected_book" in st.session_state:
        book = st.session_state["selected_book"]
        st.write("## 📖 Book Details")
        st.image(book["thumbnail"], width=150)
        st.write(f"**Title:** {book['title']}")
        st.write(f"**Author:** {book['author']}")
        st.write(f"**Source:** {book['source']}")
        st.write(f"**Description:** {book['description']}")
        if st.button("❌ Close"):
            del st.session_state["selected_book"]
# ---- View All Books UI ----

def show_all_books():
    st.subheader("📙📕📗📘📔 All Available Books")

    # Add CSS for better card styling
    st.markdown("""
        <style>
            .book-container {
                display: flex;
                flex-wrap: wrap;
                justify-content: center;
                gap: 20px;
            }
            .book-card {
                background: #DDA0DD;
                padding: 15px;
                border-radius: 12px;
                text-align: center;
                box-shadow: 2px 4px 8px rgba(0, 0, 0, 0.2);
                margin-bottom: 15px;
                min-height: 320px;
                max-width: 230px;
                display: inline-block;
                transition: transform 0.2s ease-in-out;
            }
            .book-card:hover {
                transform: scale(1.05);
            }
            .card-image {
                max-width: 150px;
                height: auto;
                border-radius: 8px;
                margin-bottom: 10px;
            }
            .card-title {
                font-weight: bold;
                font-size: 18px;
                color: #000;
            }
            .card-author {
                font-size: 14px;
                color: #333;
                margin-bottom: 8px;
            }
            .wishlist-btn, .view-btn {
                border: none;
                padding: 8px;
                font-size: 14px;
                border-radius: 5px;
                cursor: pointer;
                margin: 5px;
                width: 85%;
            }
            .wishlist-btn {
                background: #ff4b5c;
                color: white;
            }
            .view-btn {
                background: #007bff;
                color: white;
            }
            .wishlist-btn:hover {
                background: #e33b4a;
            }
            .view-btn:hover {
                background: #0056b3;
            }
        </style>
    """, unsafe_allow_html=True)

    # Fetch books from API
    response = requests.get(f"{BASE_URL}/books")

    if response.status_code == 200:
        books = response.json()
        
        st.markdown('<div class="book-container">', unsafe_allow_html=True)

        for book in books:
            image_data = book.get("thumbnail")  # Assuming 'thumbnail' contains base64 string
            if image_data:
                image_bytes = base64.b64decode(image_data)
                image_url = f"data:image/jpeg;base64,{image_bytes}"
            else:
                image_url = "https://via.placeholder.com/100x150"

            st.markdown(f"""
                <div class="book-card">
                    <img src="{image_url}" class="card-image">
                    <div class="card-title">{book['title']}</div>
                    <div class="card-author">Author: {book['author']}</div>
                    <div class="card-author">Genre: {book['genre']}</div>
                    <button class="view-btn">🔍 View</button>
                    <button class="wishlist-btn">❤️ Wishlist</button>
                </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.error("❌ Failed to fetch books.")



# ---- Library UI ----
def library_ui():
    st.title("📚 Personal Library Manager")

    # Sidebar Menu
    with st.sidebar:
        st.title("Menu")
        choice = st.radio(
            "Select an option",
            ["Add Book", "Remove Book", "Update Book", "Search Book", "View All Books", "Analytics", "Recommendations", "Data Management"],
            index=0
        )

        # Wishlist Display
        st.subheader("📥 Wishlist")
        wishlist = get_wishlist()
        if wishlist:
            for item in wishlist:
                st.write(f"- {item}")
        else:
            st.write("Your wishlist is empty.")

    if choice == "Add Book":
        add_book_ui()
    elif choice == "Remove Book":
        remove_book_ui()
    elif choice == "Update Book":
        update_book_ui()
    elif choice == "Search Book":
        search_book_ui()
    elif choice == "View All Books":
        show_all_books()
    elif choice == "Analytics":
        show_analytics()
    elif choice == "Recommendations":
        show_recommendations()
    elif choice == "Data Management":
        data_management()

# ---- Main App Logic ----
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "show_login" not in st.session_state:
    st.session_state["show_login"] = True

# Theme Selection
theme = st.sidebar.selectbox("Select Theme", ["light", "dark"])
st.markdown(f"""

""", unsafe_allow_html=True)

# Main UI
if not st.session_state["logged_in"]:
    choice = st.radio("Select an option", ["Sign Up", "Login"], horizontal=True)
    if choice == "Login":
        login_ui()
    else:
        signup_ui()
else:
    library_ui()