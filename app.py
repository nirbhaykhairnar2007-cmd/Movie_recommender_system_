import pickle
import streamlit as st
import os
import requests

st.set_page_config(page_title="Movie Recommender", layout="wide")


@st.cache_data
def load_data():
    movies = pickle.load(open(os.path.join(os.path.dirname(__file__), '../3_Models/movies.pkl'), 'rb'))
    similarity = pickle.load(open('3_Models/similarity.pkl', 'rb'))
    return movies, similarity

movies, similarity = load_data()

TMDB_API_KEY = "40d473a68eef3fff5ab493f29a4fac7f"


@st.cache_data
def fetch_movie_details(movie_id):

    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"

    try:
        response = requests.get(url, timeout=3)

        if response.status_code != 200:
            raise Exception("API error")

        data = response.json()

        poster_path = data.get("poster_path")

        poster_url = (
            f"https://image.tmdb.org/t/p/w500{poster_path}"
            if poster_path
            else "https://via.placeholder.com/300x450"
        )

        return {
            "poster": poster_url,
            "title": data.get("original_title", "Unknown"),
            "release_date": data.get("release_date", "N/A"),
            "rating": data.get("vote_average", "N/A"),
            "overview": data.get("overview", "No description available."),
            "tagline": data.get("tagline", ""),
            "runtime": data.get("runtime", 0),
            "genres": [g["name"] for g in data.get("genres", [])]
        }

    except:
        return {
            "poster": "https://via.placeholder.com/300x450",
            "title": "Unknown",
            "release_date": "N/A",
            "rating": "N/A",
            "overview": "No description available.",
            "tagline": "",
            "runtime": 0,
            "genres": []
        }


def get_movie_details(movie_id):

    movie = movies[movies['id'] == movie_id].iloc[0]

    details = {
        "poster": movie.get("poster_url"),
        "title": movie.get("original_title"),
        "release_date": movie.get("release_date"),
        "rating": movie.get("rating"),
        "overview": movie.get("overview"),
        "tagline": movie.get("tagline"),
        "runtime": movie.get("runtime"),
        "genres": movie.get("genres").split(", ") if movie.get("genres") else []
    }

    if not details["poster"] or details["poster"] == "N/A":
        return fetch_movie_details(movie_id)

    return details


def recommend(movie, n=10):

    try:
        index = movies[movies['original_title'] == movie].index[0]
    except:
        return []

    distances = similarity[index]

    movie_list = sorted(
        list(enumerate(distances)),
        reverse=True,
        key=lambda x: x[1]
    )[1:n+1]

    recommended = []

    for i in movie_list:
        movie_id = movies.iloc[i[0]].id
        recommended.append(get_movie_details(movie_id))

    return recommended


if "selected_movie" not in st.session_state:

    st.header("🎬 Movie Recommender System")

    selected_movie_name = st.selectbox(
        "Search for a Movie",
        movies['original_title'].values
    )

    if st.button("Search"):
        st.session_state.selected_movie = selected_movie_name
        st.rerun()


    movies_per_page = 20
    total_movies = len(movies)
    total_pages = (total_movies // movies_per_page) + 1

    if "current_page" not in st.session_state:
        st.session_state.current_page = 1

    nav_cols = st.columns([1,6,1])

    with nav_cols[0]:
        if st.button("⬅ Prev") and st.session_state.current_page > 1:
            st.session_state.current_page -= 1
            st.rerun()

    with nav_cols[1]:
        st.markdown(f"### Page {st.session_state.current_page} / {total_pages}")

    with nav_cols[2]:
        if st.button("Next ➡") and st.session_state.current_page < total_pages:
            st.session_state.current_page += 1
            st.rerun()

    start_idx = (st.session_state.current_page - 1) * movies_per_page
    end_idx = start_idx + movies_per_page

    page_movies = movies.iloc[start_idx:end_idx]

    cols = st.columns(5)

    for i, movie in enumerate(page_movies.itertuples()):

        with cols[i % 5]:

            details = get_movie_details(movie.id)

            st.image(details["poster"], width=150)

            if st.button(movie.original_title, key=f"title_{start_idx+i}"):

                st.session_state.selected_movie = movie.original_title
                st.rerun()


else:

    selected_movie = st.session_state.selected_movie

    st.title(f"🎥 {selected_movie}")

    movie_id = movies[movies['original_title'] == selected_movie].iloc[0].id

    details = get_movie_details(movie_id)

    col1, col2 = st.columns([1,2])

    with col1:
        st.image(details["poster"], width=300)

    with col2:

        if details["tagline"]:
            st.subheader(details["tagline"])

        st.write(f"⭐ Rating: {details['rating']}")
        st.write(f"📅 Release Date: {details['release_date']}")
        st.write(f"🎭 Genres: {', '.join(details['genres'])}")
        st.write(f"⏱ Runtime: {details['runtime']} min")
        st.write(details["overview"])

    st.subheader("✨ Recommended Movies")

    recommended_movies = recommend(selected_movie)

    for row in range(0, 10, 5):

        cols = st.columns(5)

        for i in range(5):

            idx = row + i

            if idx < len(recommended_movies):

                movie = recommended_movies[idx]

                with cols[i]:

                    st.image(movie["poster"], width=150)

                    if st.button(movie["title"], key=f"rec_{idx}"):

                        st.session_state.selected_movie = movie["title"]
                        st.rerun()

    if st.button("⬅ Back to All Movies"):
        del st.session_state.selected_movie
        st.rerun()