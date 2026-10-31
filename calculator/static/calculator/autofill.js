document.addEventListener('DOMContentLoaded', function() {
    const nameInput = document.getElementById('id_name');
    
    if (nameInput) {
        // 'blur' means the user clicked out of the text box or hit the Tab key
        nameInput.addEventListener('blur', function() {
            // Convert to lowercase for the API (e.g. "Swampert" -> "swampert")
            const pokemonName = this.value.trim().toLowerCase().replace(' ', '-');
            if (!pokemonName) return;

            fetch(`https://pokeapi.co/api/v2/pokemon/${pokemonName}`)
                .then(response => {
                    if (response.ok) return response.json();
                    throw new Error('Pokemon not found');
                })
                .then(data => {
                    // Map the stats from the API to a clean dictionary
                    const stats = {};
                    data.stats.forEach(s => {
                        stats[s.stat.name] = s.base_stat;
                    });
                    
                    // Autofill the Django admin boxes using their auto-generated IDs
                    document.getElementById('id_base_hp').value = stats['hp'] || 0;
                    document.getElementById('id_base_attack').value = stats['attack'] || 0;
                    document.getElementById('id_base_defense').value = stats['defense'] || 0;
                    document.getElementById('id_base_sp_atk').value = stats['special-attack'] || 0;
                    document.getElementById('id_base_sp_def').value = stats['special-defense'] || 0;
                })
                .catch(error => {
                    console.log("Could not fetch stats, check your spelling:", error);
                });
        });
    }
});