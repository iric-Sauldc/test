document.addEventListener('DOMContentLoaded', async () => {
    const tableBody = document.querySelector('#ranking-table tbody');
    const searchInput = document.getElementById('search');
    const sortSelect = document.getElementById('sort');  // Elemento select para ordenación
    let currentRankingData = []; // Variable para almacenar los datos actuales del ranking

    // Función para renderizar la tabla
    const renderRankingTable = (data) => {
        tableBody.innerHTML = ''; // Limpia la tabla antes de renderizar
        data.forEach((participant) => {
            const row = `
                <tr>
                    <td>${participant.posicion}</td>
                    <td><a href="/ranking/${participant.id}">${participant.nombre}</a></td>
                    <td>${participant.puntuacion}</td>
                    <td>${participant.desafios_completados}</td>
                    <td>${participant.tiempo_total}</td>
                    <td>${participant.penalizaciones}</td>
                </tr>
            `;
            tableBody.insertAdjacentHTML('beforeend', row);
        });
    };

    // Función para filtrar el ranking
    const filterRanking = (query) => {
        const filteredData = currentRankingData.filter(participant =>
            participant.nombre.toLowerCase().includes(query.toLowerCase())
        );
        sortRankingData(filteredData);  // Ordena los datos después de filtrar
    };

    // Función para ordenar los datos del ranking
    const sortRankingData = (data) => {
        const sortBy = sortSelect.value;
        let sortedData = [...data];  // Copia del array para no mutar el original

        // Ordenar los datos según la opción seleccionada
        switch (sortBy) {
            case 'puntuacion':
                sortedData.sort((a, b) => b.puntuacion - a.puntuacion);  // Orden descendente por puntuación
                break;
            case 'tiempo_total':
                sortedData.sort((a, b) => a.tiempo_total - b.tiempo_total);  // Orden ascendente por tiempo
                break;
            case 'desafios_completados':
                sortedData.sort((a, b) => b.desafios_completados - a.desafios_completados);  // Orden descendente por desafíos completados
                break;
            default:
                break;
        }

        renderRankingTable(sortedData);  // Renderiza la tabla con los datos ordenados
    };

    // Función para obtener los datos del ranking
    const fetchRankingData = async () => {
        try {
            const response = await fetch('/ranking/data');
            if (response.ok) {
                const newRankingData = await response.json();
                // Compara con los datos actuales antes de actualizar
                if (JSON.stringify(currentRankingData) !== JSON.stringify(newRankingData)) {
                    console.log('Datos del ranking actualizados');
                    currentRankingData = newRankingData; // Actualiza la variable con los nuevos datos
                    const query = searchInput.value.toLowerCase(); // Obtiene el filtro actual
                    filterRanking(query); // Filtra y renderiza
                } else {
                    console.log('Datos del ranking sin cambios');
                }
            } else {
                console.error('Error al obtener los datos del ranking');
            }
        } catch (error) {
            console.error('Error de conexión:', error);
        }
    };

    // Cargar los datos iniciales al arrancar la página
    try {
        const response = await fetch('/ranking/data');
        if (response.ok) {
            currentRankingData = await response.json(); // Inicializa la variable con los datos del servidor
            sortRankingData(currentRankingData); // Ordena los datos por defecto
        } else {
            console.error('Error al cargar los datos iniciales');
        }
    } catch (error) {
        console.error('Error al cargar los datos iniciales:', error);
    }

    // Actualizar los datos periódicamente
    setInterval(fetchRankingData, 5000);

    // Filtrar resultados en tiempo real mientras se escribe
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();
        filterRanking(query);
    });

    // Ordenar la tabla cuando cambia la opción de orden
    sortSelect.addEventListener('change', () => {
        sortRankingData(currentRankingData);  // Vuelve a ordenar con los datos actuales
    });
});
