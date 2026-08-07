import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.neighbors import NearestNeighbors


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Movie Recommendation System",
    page_icon="🎬",
    layout="wide"
)


# --------------------------------------------------
# CUSTOM CSS
# --------------------------------------------------

st.markdown("""
<style>

.main-title {
    font-size: 42px;
    font-weight: 700;
    text-align: center;
    margin-bottom: 10px;
}

.subtitle {
    text-align: center;
    font-size: 18px;
    color: #666;
    margin-bottom: 30px;
}

.recommendation-card {
    padding: 18px;
    border-radius: 10px;
    border: 1px solid #ddd;
    margin-bottom: 12px;
}

</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

@st.cache_data
def load_data():

    movies = pd.read_csv("data/movies.csv")
    ratings = pd.read_csv("data/ratings.csv")

    return movies, ratings


movies, ratings = load_data()


# --------------------------------------------------
# BUILD RECOMMENDATION MODEL
# --------------------------------------------------

@st.cache_resource
def build_model(ratings):

    user_movie_matrix = ratings.pivot_table(
        index="userId",
        columns="movieId",
        values="rating"
    )

    movie_user_matrix = user_movie_matrix.T

    movie_user_matrix_filled = movie_user_matrix.fillna(0)

    model = NearestNeighbors(
        metric="cosine",
        algorithm="brute",
        n_neighbors=11
    )

    model.fit(movie_user_matrix_filled)

    return model, movie_user_matrix_filled


model, movie_user_matrix = build_model(ratings)


# --------------------------------------------------
# RECOMMENDATION FUNCTION
# --------------------------------------------------

def recommend_movies(movie_title, n=10):

    movie_data = movies[
        movies["title"].str.lower() == movie_title.lower()
    ]

    if movie_data.empty:
        return pd.DataFrame()

    movie_id = movie_data.iloc[0]["movieId"]

    if movie_id not in movie_user_matrix.index:
        return pd.DataFrame()

    movie_position = movie_user_matrix.index.get_loc(movie_id)

    movie_vector = movie_user_matrix.iloc[
        movie_position
    ].values.reshape(1, -1)

    distances, indices = model.kneighbors(
        movie_vector,
        n_neighbors=n + 1
    )

    recommended_movie_ids = movie_user_matrix.index[
        indices[0][1:]
    ]

    similarity_scores = 1 - distances[0][1:]

    recommendations = movies[
        movies["movieId"].isin(recommended_movie_ids)
    ].copy()

    score_df = pd.DataFrame({
        "movieId": recommended_movie_ids,
        "similarity": similarity_scores
    })

    recommendations = recommendations.merge(
        score_df,
        on="movieId"
    )

    recommendations = recommendations.sort_values(
        "similarity",
        ascending=False
    )

    recommendations["similarity"] = (
        recommendations["similarity"] * 100
    ).round(2)

    return recommendations[
        ["title", "genres", "similarity"]
    ]


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.markdown(
    '<div class="main-title">🎬 Movie Recommendation System</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Discover movies similar to your favorites using '
    'collaborative filtering'
    '</div>',
    unsafe_allow_html=True
)


# --------------------------------------------------
# MOVIE SELECTION
# --------------------------------------------------

st.subheader("🎥 Find Your Next Movie")

movie_titles = sorted(
    movies["title"].dropna().unique()
)

selected_movie = st.selectbox(
    "Select a movie you like:",
    movie_titles
)

recommend_button = st.button(
    "🎬 Recommend Movies",
    use_container_width=True
)


# --------------------------------------------------
# RECOMMENDATIONS
# --------------------------------------------------

if recommend_button:

    recommendations = recommend_movies(
        selected_movie,
        10
    )

    if recommendations.empty:

        st.warning(
            "Sorry, recommendations could not be generated."
        )

    else:

        st.success(
            f"Movies similar to **{selected_movie}**"
        )

        for i, row in recommendations.iterrows():

            st.markdown(
                f"""
                <div class="recommendation-card">

                <h4>🎬 {row['title']}</h4>

                <p>
                <b>Genre:</b> {row['genres']}
                </p>

                <p>
                <b>Similarity:</b> {row['similarity']}%
                </p>

                </div>
                """,
                unsafe_allow_html=True
            )


# --------------------------------------------------
# ANALYTICS
# --------------------------------------------------

st.divider()

st.header("📊 Movie Analytics")


col1, col2 = st.columns(2)


# Rating distribution

with col1:

    st.subheader("⭐ Rating Distribution")

    fig, ax = plt.subplots(
        figsize=(8, 5)
    )

    sns.countplot(
        data=ratings,
        x="rating",
        ax=ax
    )

    ax.set_xlabel("Rating")
    ax.set_ylabel("Number of Ratings")

    st.pyplot(fig)


# Popular movies

with col2:

    st.subheader("🔥 Most Rated Movies")

    movie_counts = (
        ratings.groupby("movieId")
        .size()
        .reset_index(name="rating_count")
    )

    popular_movies = movie_counts.merge(
        movies,
        on="movieId"
    )

    popular_movies = popular_movies.sort_values(
        "rating_count",
        ascending=False
    ).head(10)

    fig, ax = plt.subplots(
        figsize=(8, 5)
    )

    sns.barplot(
        data=popular_movies,
        x="rating_count",
        y="title",
        ax=ax
    )

    ax.set_xlabel("Number of Ratings")
    ax.set_ylabel("Movie")

    st.pyplot(fig)


# --------------------------------------------------
# GENRE ANALYSIS
# --------------------------------------------------

st.subheader("🎭 Popular Movie Genres")

genre_counts = (
    movies["genres"]
    .str.split("|")
    .explode()
    .value_counts()
    .head(10)
)

fig, ax = plt.subplots(
    figsize=(12, 5)
)

sns.barplot(
    x=genre_counts.values,
    y=genre_counts.index,
    ax=ax
)

ax.set_xlabel("Number of Movies")
ax.set_ylabel("Genre")

st.pyplot(fig)


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "Built with Python, Pandas, Scikit-learn and Streamlit "
    "using the MovieLens dataset."
)

