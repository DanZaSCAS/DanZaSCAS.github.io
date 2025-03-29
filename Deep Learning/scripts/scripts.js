// Store songs in localStorage
let songs = JSON.parse(localStorage.getItem('songs')) || [];

// DOM Elements
const songGrid = document.getElementById('songGrid');
const addSongBtn = document.getElementById('addSongBtn');
const modal = document.getElementById('addSongModal');
const closeBtn = document.querySelector('.close');
const addSongForm = document.getElementById('addSongForm');
const searchInput = document.getElementById('searchInput');

// Display songs
function displaySongs(songsToDisplay = songs) {
    songGrid.innerHTML = '';
    songsToDisplay.forEach(song => {
        const songCard = document.createElement('div');
        songCard.className = 'song-card';
        songCard.innerHTML = `
            <h3>${song.title}</h3>
            <p>Artist: ${song.artist}</p>
            <p>Genre: ${song.genre}</p>
            <p>Year: ${song.year}</p>
        `;
        songGrid.appendChild(songCard);
    });
}

// Add new song
addSongForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const newSong = {
        title: addSongForm.title.value,
        artist: addSongForm.artist.value,
        genre: addSongForm.genre.value,
        year: addSongForm.year.value
    };
    songs.push(newSong);
    localStorage.setItem('songs', JSON.stringify(songs));
    displaySongs();
    modal.style.display = 'none';
    addSongForm.reset();
});

// Search functionality
searchInput.addEventListener('input', (e) => {
    const searchTerm = e.target.value.toLowerCase();
    const filteredSongs = songs.filter(song => 
        song.title.toLowerCase().includes(searchTerm) ||
        song.artist.toLowerCase().includes(searchTerm)
    );
    displaySongs(filteredSongs);
});

// Modal controls
addSongBtn.onclick = () => modal.style.display = 'block';
closeBtn.onclick = () => modal.style.display = 'none';
window.onclick = (e) => {
    if (e.target === modal) modal.style.display = 'none';
};

// Initial display
displaySongs();