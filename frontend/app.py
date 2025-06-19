import streamlit as st
import requests
import jwt
from datetime import datetime, timedelta, date
import pandas as pd

API_URL = "http://localhost:8000/api"

st.set_page_config(
    page_title="Library Management System",
    layout="wide"
)

if 'token' not in st.session_state:
    st.session_state.token = None
if 'role' not in st.session_state:
    st.session_state.role = None
if 'username' not in st.session_state:
    st.session_state.username = None

def get_headers():
    """Get authorization headers"""
    if st.session_state.token:
        return {"Authorization": f"Bearer {st.session_state.token}"}
    return {}

def handle_api_error(response):
    """Handle API errors with user-friendly messages"""
    if response.status_code == 401:
        st.error("Session expired. Please login again.")
        st.session_state.token = None
        st.session_state.role = None
        st.session_state.username = None
        st.rerun()
    elif response.status_code == 403:
        st.error("You don't have permission to perform this action.")
    elif response.status_code == 400:
        try:
            errors = response.json()
            for field, messages in errors.items():
                if isinstance(messages, list):
                    st.error(f"{field}: {', '.join(messages)}")
                else:
                    st.error(f"{field}: {messages}")
        except:
            st.error("Invalid request. Please check your input.")
    else:
        st.error(f"An error occurred: {response.text}")

def login_register_page():
    """Login and registration page"""
    st.title("  Library Management System")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type='password')
            submit = st.form_submit_button("Login")
            
            if submit and username and password:
                try:
                    response = requests.post(
                        f"{API_URL}/login/", 
                        json={'username': username, 'password': password}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.token = data['access']
                        st.session_state.username = username
                        
                        # Decode JWT to get role
                        try:
                            decoded = jwt.decode(
                                st.session_state.token, 
                                options={"verify_signature": False}
                            )
                            st.session_state.role = decoded.get("role", "user")
                        except:
                            st.session_state.role = "user"
                        
                        st.success("Logged in successfully!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                except requests.exceptions.RequestException:
                    st.error("Could not connect to server. Please try again.")
    
    with tab2:
        st.subheader("Register")
        with st.form("register_form"):
            new_username = st.text_input("Username", key="reg_username")
            email = st.text_input("Email", key="reg_email")
            new_password = st.text_input("Password", type='password', key="reg_password")
            role = st.selectbox("Role", ["user", "librarian"], key="reg_role")
            submit_reg = st.form_submit_button("Register")
            
            if submit_reg and new_username and email and new_password:
                try:
                    response = requests.post(
                        f"{API_URL}/register/", 
                        json={
                            'username': new_username,
                            'email': email,
                            'password': new_password,
                            'role': role
                        }
                    )
                    
                    if response.status_code == 201:
                        st.success("Registration successful! You can now login.")
                    else:
                        handle_api_error(response)
                except requests.exceptions.RequestException:
                    st.error("Could not connect to server. Please try again.")

def display_books():
    """Display books with search and pagination"""
    st.subheader(" Books")
    
    # Search and filters
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        search_query = st.text_input("🔍 Search books by title, author, or genre", key="book_search")
    with col2:
        show_only_available = st.checkbox("Available only", key="available_filter")
    with col3:
        page = st.number_input("Page", min_value=1, value=1, step=1, key="book_page")
    
    # Build API URL
    url = f"{API_URL}/books/"
    params = {"page": page}
    if search_query:
        params["search"] = search_query
    if show_only_available:
        params["available"] = "true"
    
    try:
        response = requests.get(url, headers=get_headers(), params=params)
        
        if response.status_code == 200:
            data = response.json()
            books = data.get('results', [])
            total_count = data.get('count', 0)
            
            if books:
                st.info(f"Found {total_count} books")
                
                for book in books:
                    with st.container():
                        col1, col2, col3 = st.columns([3, 1, 2])
                        
                        with col1:
                            availability = "Available" if book['available'] else "Not Available"
                            st.markdown(f"""
                            **{book['title']}**  
                            *by {book['author']}*  
                            Genre: {book['genre']}  
                            Status: {availability}
                            """)
                        
                        with col2:
                            if st.session_state.role == "user" and book['available']:
                                if st.button("  Borrow", key=f"borrow_{book['id']}"):
                                    borrow_book(book['id'])
                        
                        with col3:
                            if st.session_state.role == "librarian":
                                col3a, col3b = st.columns(2)
                                with col3a:
                                    if st.button("Edit", key=f"edit_{book['id']}"):
                                        st.session_state[f"editing_{book['id']}"] = True
                                with col3b:
                                    if st.button("Delete", key=f"delete_{book['id']}"):
                                        delete_book(book['id'])
                        
                        # Edit form
                        if st.session_state.get(f"editing_{book['id']}", False):
                            with st.form(f"edit_form_{book['id']}"):
                                new_title = st.text_input("Title", value=book['title'])
                                new_author = st.text_input("Author", value=book['author'])
                                new_genre = st.text_input("Genre", value=book['genre'])
                                
                                col_save, col_cancel = st.columns(2)
                                with col_save:
                                    if st.form_submit_button("Save"):
                                        update_book(book['id'], new_title, new_author, new_genre)
                                        st.session_state[f"editing_{book['id']}"] = False
                                        st.rerun()
                                with col_cancel:
                                    if st.form_submit_button("Cancel"):
                                        st.session_state[f"editing_{book['id']}"] = False
                                        st.rerun()
                        
                        st.divider()
            else:
                st.info("No books found")
        else:
            handle_api_error(response)
    except requests.exceptions.RequestException:
        st.error("Could not fetch books. Please check your connection.")

def borrow_book(book_id):
    """Borrow a book"""
    due_date = date.today() + timedelta(days=14)
    
    try:
        response = requests.post(
            f"{API_URL}/borrows/",
            headers=get_headers(),
            json={
                "book": book_id,
                "due_date": due_date.isoformat()
            }
        )
        
        if response.status_code == 201:
            st.success("Book borrowed successfully! Due date: " + due_date.strftime("%Y-%m-%d"))
            st.rerun()
        else:
            handle_api_error(response)
    except requests.exceptions.RequestException:
        st.error("Could not borrow book. Please try again.")

def update_book(book_id, title, author, genre):
    """Update a book"""
    try:
        response = requests.put(
            f"{API_URL}/books/{book_id}/",
            headers=get_headers(),
            json={
                "title": title,
                "author": author,
                "genre": genre
            }
        )
        
        if response.status_code == 200:
            st.success("Book updated successfully!")
        else:
            handle_api_error(response)
    except requests.exceptions.RequestException:
        st.error("Could not update book. Please try again.")

def delete_book(book_id):
    """Delete a book"""
    try:
        response = requests.delete(
            f"{API_URL}/books/{book_id}/",
            headers=get_headers()
        )
        
        if response.status_code == 204:
            st.success("Book deleted successfully!")
            st.rerun()
        else:
            handle_api_error(response)
    except requests.exceptions.RequestException:
        st.error("Could not delete book. Please try again.")

def add_book_form():
    """Form to add new book"""
    if st.session_state.role != "librarian":
        return
    
    st.subheader("Add New Book")
    with st.form("add_book_form"):
        title = st.text_input("Title")
        author = st.text_input("Author")
        genre = st.text_input("Genre")
        submit = st.form_submit_button("Add Book")
        
        if submit and title and author and genre:
            try:
                response = requests.post(
                    f"{API_URL}/books/",
                    headers=get_headers(),
                    json={
                        "title": title,
                        "author": author,
                        "genre": genre,
                        "available": True
                    }
                )
                
                if response.status_code == 201:
                    st.success("Book added successfully!")
                    st.rerun()
                else:
                    handle_api_error(response)
            except requests.exceptions.RequestException:
                st.error("Could not add book. Please try again.")

def display_borrowed_books():
    """Display user's borrowed books"""
    st.subheader("  My Borrowed Books")
    
    try:
        response = requests.get(f"{API_URL}/borrows/my_borrows/", headers=get_headers())
        
        if response.status_code == 200:
            data = response.json()
            borrows = data.get('results', []) if 'results' in data else data
            
            if borrows:
                for borrow in borrows:
                    if not borrow.get('returned', False):
                        with st.container():
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                book_title = borrow.get('book_title', 'Unknown Title')
                                book_author = borrow.get('book_author', 'Unknown Author')
                                due_date = borrow.get('due_date', 'Unknown')
                                borrowed_date = borrow.get('borrowed_at', '').split('T')[0] if borrow.get('borrowed_at') else 'Unknown'
                                
                                # Check if overdue
                                is_overdue = False
                                if due_date != 'Unknown':
                                    try:
                                        due_date_obj = datetime.strptime(due_date, '%Y-%m-%d').date()
                                        is_overdue = due_date_obj < date.today()
                                    except:
                                        pass
                                
                                status_text = "OVERDUE" if is_overdue else "Active"
                                
                                st.markdown(f"""
                                **{book_title}**  
                                *by {book_author}*  
                                Borrowed: {borrowed_date}  
                                Due: {due_date} ({status_text})
                                """)
                            
                            with col2:
                                if st.button("Return", key=f"return_{borrow['id']}"):
                                    return_book(borrow['id'])
                            
                            st.divider()
            else:
                st.info("You haven't borrowed any books yet.")
        else:
            handle_api_error(response)
    except requests.exceptions.RequestException:
        st.error("Could not fetch borrowed books. Please check your connection.")

def return_book(borrow_id):
    """Return a borrowed book"""
    try:
        response = requests.patch(
            f"{API_URL}/borrows/{borrow_id}/",
            headers=get_headers(),
            json={"returned": True}
        )
        
        if response.status_code == 200:
            st.success("Book returned successfully!")
            st.rerun()
        else:
            handle_api_error(response)
    except requests.exceptions.RequestException:
        st.error("Could not return book. Please try again.")

def librarian_dashboard():
    """Dashboard for librarians"""
    if st.session_state.role != "librarian":
        return
    
    st.subheader("Librarian Dashboard")
    
    # Statistics
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        # Get all books
        books_response = requests.get(f"{API_URL}/books/", headers=get_headers())
        total_books = 0
        available_books = 0
        
        if books_response.status_code == 200:
            books_data = books_response.json()
            if 'count' in books_data:
                total_books = books_data['count']
                # Get available books count
                available_response = requests.get(f"{API_URL}/books/?available=true", headers=get_headers())
                if available_response.status_code == 200:
                    available_data = available_response.json()
                    available_books = available_data.get('count', 0)
        
        # Get all borrows
        borrows_response = requests.get(f"{API_URL}/borrows/", headers=get_headers())
        active_borrows = 0
        overdue_borrows = 0
        
        if borrows_response.status_code == 200:
            borrows_data = borrows_response.json()
            borrows = borrows_data.get('results', []) if 'results' in borrows_data else borrows_data
            
            today = date.today()
            for borrow in borrows:
                if not borrow.get('returned', False):
                    active_borrows += 1
                    due_date = borrow.get('due_date')
                    if due_date:
                        try:
                            due_date_obj = datetime.strptime(due_date, '%Y-%m-%d').date()
                            if due_date_obj < today:
                                overdue_borrows += 1
                        except:
                            pass
        
        with col1:
            st.metric("  Total Books", total_books)
        with col2:
            st.metric("Available Books", available_books)
        with col3:
            st.metric(" Active Borrows", active_borrows)
        with col4:
            st.metric("Overdue Books", overdue_borrows)
        
        # Overdue books section
        if overdue_borrows > 0:
            st.subheader("Overdue Books")
            try:
                overdue_response = requests.get(f"{API_URL}/borrows/overdue/", headers=get_headers())
                if overdue_response.status_code == 200:
                    overdue_data = overdue_response.json()
                    overdue_list = overdue_data.get('results', []) if 'results' in overdue_data else overdue_data
                    
                    for borrow in overdue_list:
                        book_title = borrow.get('book_title', 'Unknown Title')
                        user_username = borrow.get('user_username', 'Unknown User')
                        due_date = borrow.get('due_date', 'Unknown')
                        days_overdue = 0
                        
                        if due_date != 'Unknown':
                            try:
                                due_date_obj = datetime.strptime(due_date, '%Y-%m-%d').date()
                                days_overdue = (date.today() - due_date_obj).days
                            except:
                                pass
                        
                        st.error(f" **{book_title}** - Borrowed by: {user_username} - Due: {due_date} ({days_overdue} days overdue)")
            except requests.exceptions.RequestException:
                st.error("Could not fetch overdue books.")
    
    except requests.exceptions.RequestException:
        st.error("Could not fetch dashboard data.")

def main():
    """Main application"""
    # Check if user is logged in
    if not st.session_state.token:
        login_register_page()
        return
    
    # Sidebar
    with st.sidebar:
        st.success(f"Logged in as: **{st.session_state.username}** ({st.session_state.role})")
        
        if st.button("Logout"):
            st.session_state.token = None
            st.session_state.role = None
            st.session_state.username = None
            st.rerun()
        
        st.divider()
        
        # Navigation
        if st.session_state.role == "librarian":
            page = st.selectbox(
                "  Navigation", 
                ["Dashboard", "Books", "Add Book", "All Borrows"],
                key="librarian_nav"
            )
        else:
            page = st.selectbox(
                "  Navigation", 
                ["Books", "My Borrowed Books"],
                key="user_nav"
            )
    
    # Main content
    st.title("  Library Management System")
    
    if st.session_state.role == "librarian":
        if page == "Dashboard":
            librarian_dashboard()
        elif page == "Books":
            display_books()
        elif page == "Add Book":
            add_book_form()
        elif page == "All Borrows":
            display_all_borrows()
    else:
        if page == "Books":
            display_books()
        elif page == "My Borrowed Books":
            display_borrowed_books()

def display_all_borrows():
    """Display all borrows for librarian"""
    if st.session_state.role != "librarian":
        return
    
    st.subheader("  All Borrows")
    
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        show_returned = st.checkbox("Include returned books", key="show_returned_filter")
    with col2:
        page = st.number_input("Page", min_value=1, value=1, step=1, key="borrows_page")
    
    try:
        params = {"page": page}
        response = requests.get(f"{API_URL}/borrows/", headers=get_headers(), params=params)
        
        if response.status_code == 200:
            data = response.json()
            borrows = data.get('results', []) if 'results' in data else data
            total_count = data.get('count', len(borrows))
            
            if borrows:
                st.info(f"Total borrows: {total_count}")
                
                # Create DataFrame for better display
                borrow_data = []
                for borrow in borrows:
                    if not show_returned and borrow.get('returned', False):
                        continue
                    
                    book_title = borrow.get('book_title', 'Unknown Title')
                    user_username = borrow.get('user_username', 'Unknown User')
                    borrowed_date = borrow.get('borrowed_at', '').split('T')[0] if borrow.get('borrowed_at') else 'Unknown'
                    due_date = borrow.get('due_date', 'Unknown')
                    returned = "Yes" if borrow.get('returned', False) else "No"
                    returned_date = borrow.get('returned_at', '').split('T')[0] if borrow.get('returned_at') else '-'
                    
                    # Check if overdue
                    status = "Active"
                    if borrow.get('returned', False):
                        status = "Returned"
                    elif due_date != 'Unknown':
                        try:
                            due_date_obj = datetime.strptime(due_date, '%Y-%m-%d').date()
                            if due_date_obj < date.today():
                                status = "Overdue"
                        except:
                            pass
                    
                    borrow_data.append({
                        'Book Title': book_title,
                        'User': user_username,
                        'Borrowed Date': borrowed_date,
                        'Due Date': due_date,
                        'Status': status,
                        'Returned': returned,
                        'Returned Date': returned_date
                    })
                
                if borrow_data:
                    df = pd.DataFrame(borrow_data)
                    
                    # Color code the status
                    def highlight_status(val):
                        if val == 'Overdue':
                            return 'background-color: #ffcccc'
                        elif val == 'Returned':
                            return 'background-color: #ccffcc'
                        else:
                            return 'background-color: #ffffcc'
                    
                    styled_df = df.style.applymap(highlight_status, subset=['Status'])
                    st.dataframe(styled_df, use_container_width=True)
                else:
                    st.info("No borrows match the current filters.")
            else:
                st.info("No borrows found.")
        else:
            handle_api_error(response)
    except requests.exceptions.RequestException:
        st.error("Could not fetch borrows. Please check your connection.")

# Custom CSS
st.markdown("""
<style>
    .stButton > button {
        width: 100%;
        border-radius: 5px;
    }
    .stSelectbox > div > div {
        background-color: #f0f2f6;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()