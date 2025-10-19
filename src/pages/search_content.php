<?php
$page = 'search';

// CONFIG
$dbHost = 'localhost';
$dbUser = 'root';
$dbPass = 'dx66ksdc';
$dbName = 'imdb';

// Connect (mysqli)
$mysqli = new mysqli($dbHost, $dbUser, $dbPass, $dbName);
if ($mysqli->connect_errno) {
    echo '<div class="container mt-4"><div class="alert alert-danger">Erro ao conectar ao banco de dados.</div></div>';
    return;
}

// SELECT
$selectedType = $_GET['type'] ?? 'movie';
?>
<div class="container mt-4 pt-0 h-100">
    <div class="title-search text-start">
        <h2>Pesquisar</h2>
    </div>

    <div class="search-card-wrapper mt-2">
        <div class="card">
            <div class="card-body">
                <div class="mb-3">
                    <label for="searchSelector" class="form-label">Pesquisar por</label>
                    <select id="searchSelector" class="form-select" aria-label="Selecionar tipo">
                        <option value="movie" <?php echo $selectedType === 'movie' ? 'selected' : ''; ?>>Filme</option>
                        <option value="actor" <?php echo $selectedType === 'actor' ? 'selected' : ''; ?>>Ator</option>
                    </select>
                </div>

                <div id="searchComponents">
                    <?php
                    include __DIR__ . '/../components/search_movie.php';
                    include __DIR__ . '/../components/search_actor.php';
                    ?>
                </div>
            </div>
        </div>
    </div>

    <div class="mt-4" id="search-results">
        <?php
        if (isset($_GET['action']) && $_GET['action'] === 'filter') {
            if (($selectedType === 'movie')) {
                $conds = [];
                $params = [];
                $types = '';

                if (!empty($_GET['title'])) {
                    $conds[] = 'f.titulo LIKE ?';
                    $params[] = '%' . $_GET['title'] . '%';
                    $types .= 's';
                }
                if (!empty($_GET['year'])) {
                    $conds[] = 'f.ano = ?';
                    $params[] = $_GET['year'];
                    $types .= 's';
                }
                if (!empty($_GET['category'])) {
                    $conds[] = 'c.descricao LIKE ?';
                    $params[] = '%' . $_GET['category'] . '%';
                    $types .= 's';
                }
                if (!empty($_GET['language'])) {
                    $conds[] = 'i.descricao LIKE ?';
                    $params[] = '%' . $_GET['language'] . '%';
                    $types .= 's';
                }
                if (!empty($_GET['rating'])) {
                    $conds[] = 'f.Classificacao_id IN (SELECT id FROM Classificacao WHERE descricao LIKE ?)';
                    $params[] = '%' . $_GET['rating'] . '%';
                    $types .= 's';
                }

                $sql = "
                    SELECT f.id, f.titulo, f.ano, c.descricao AS categoria, i.descricao AS idioma, cl.descricao AS classificacao, f.nota
                    FROM Filme f
                    LEFT JOIN Categoria c ON f.Categoria = c.id
                    LEFT JOIN Idioma i ON f.Idioma_id = i.id
                    LEFT JOIN Classificacao cl ON f.Classificacao_id = cl.id
                ";
                if (!empty($conds)) {
                    $sql .= ' WHERE ' . implode(' AND ', $conds);
                }
                $sql .= ' ORDER BY f.nota DESC, f.titulo ASC LIMIT 100';

                $stmt = $mysqli->prepare($sql);
                if ($stmt === false) {
                    echo '<div class="alert alert-danger">Erro na preparação da consulta.</div>';
                } else {
                    if (!empty($params)) {
                        $stmt->bind_param($types, ...$params);
                    }
                    $stmt->execute();
                    $res = $stmt->get_result();
                    $rows = $res->fetch_all(MYSQLI_ASSOC);
                    $stmt->close();
                    echo '<h5>Resultados de Filmes (' . count($rows) . ')</h5>';
                    if (empty($rows)) {
                        echo '<div class="alert alert-info">Nenhum filme encontrado.</div>';
                    } else {
                        echo '<div class="list-group">';
                        foreach ($rows as $row) {
                            $id = (int)$row['id'];
                            echo '<div class="list-group-item">';
                            echo '<div class="row align-items-center">';
                            echo '<div class="col-md-6"><strong>' . htmlspecialchars($row['titulo'], ENT_QUOTES) . '</strong> <br><small>' . htmlspecialchars($row['ano'] ?? 'N/A', ENT_QUOTES) . '</small></div>';
                            echo '<div class="col-md-2">' . htmlspecialchars($row['categoria'] ?? 'N/A', ENT_QUOTES) . '</div>';
                            echo '<div class="col-md-1">' . htmlspecialchars($row['idioma'] ?? 'N/A', ENT_QUOTES) . '</div>';
                            echo '<div class="col-md-1">' . htmlspecialchars($row['classificacao'] ?? 'N/A', ENT_QUOTES) . '</div>';
                            echo '<div class="col-md-1">' . (is_numeric($row['nota']) ? number_format((float)$row['nota'],1,',','.') : 'N/A') . '</div>';
                            echo '<div class="col-md-1 text-end">';
                            echo '<a href="edit_movie.php?id=' . $id . '" class="btn btn-sm btn-outline-primary me-1">Editar</a>';
                            echo '<a href="delete_movie.php?id=' . $id . '" class="btn btn-sm btn-outline-danger" onclick="return confirm(\'Confirmar exclusão deste filme?\')">Excluir</a>';
                            echo '</div>';
                            echo '</div>';
                            echo '</div>';
                        }
                        echo '</div>';
                    }
                }
            } else {
                $conds = [];
                $params = [];
                $types = '';

                if (!empty($_GET['actor_name'])) {
                    $conds[] = 'a.nome LIKE ?';
                    $params[] = '%' . $_GET['actor_name'] . '%';
                    $types .= 's';
                }
                if (!empty($_GET['actor_lastname'])) {
                    $conds[] = 'a.sobrenome LIKE ?';
                    $params[] = '%' . $_GET['actor_lastname'] . '%';
                    $types .= 's';
                }
                if (!empty($_GET['actor_nationality'])) {
                    $conds[] = 'a.nacionalidade LIKE ?';
                    $params[] = '%' . $_GET['actor_nationality'] . '%';
                    $types .= 's';
                }

                $sql = "
                    SELECT a.id, a.nome, a.sobrenome, a.data_nascimento, a.nacionalidade
                    FROM Ator a
                ";
                if (!empty($conds)) {
                    $sql .= ' WHERE ' . implode(' AND ', $conds);
                }
                $sql .= ' ORDER BY a.nome ASC LIMIT 100';

                $stmt = $mysqli->prepare($sql);
                if ($stmt === false) {
                    echo '<div class="alert alert-danger">Erro na preparação da consulta.</div>';
                } else {
                    if (!empty($params)) {
                        $stmt->bind_param($types, ...$params);
                    }
                    $stmt->execute();
                    $res = $stmt->get_result();
                    $rows = $res->fetch_all(MYSQLI_ASSOC);
                    $stmt->close();

                    echo '<h5>Resultados de Atores (' . count($rows) . ')</h5>';
                    if (empty($rows)) {
                        echo '<div class="alert alert-info">Nenhum ator encontrado.</div>';
                    } else {
                        echo '<div class="list-group">';
                        foreach ($rows as $row) {
                            $id = (int)$row['id'];
                            echo '<div class="list-group-item">';
                            echo '<div class="row align-items-center">';
                            echo '<div class="col-md-6"><strong>' . htmlspecialchars($row['nome'] . ' ' . $row['sobrenome'], ENT_QUOTES) . '</strong></div>';
                            echo '<div class="col-md-3">' . htmlspecialchars($row['data_nascimento'] ?? 'N/A', ENT_QUOTES) . '</div>';
                            echo '<div class="col-md-2">' . htmlspecialchars($row['nacionalidade'] ?? 'N/A', ENT_QUOTES) . '</div>';
                            echo '<div class="col-md-1 text-end">';
                            echo '<a href="edit_actor.php?id=' . $id . '" class="btn btn-sm btn-outline-primary me-1">Editar</a>';
                            echo '<a href="delete_actor.php?id=' . $id . '" class="btn btn-sm btn-outline-danger" onclick="return confirm(\'Confirmar exclusão deste ator?\')">Excluir</a>';
                            echo '</div>';
                            echo '</div>';
                            echo '</div>';
                        }
                        echo '</div>';
                    }
                }
            }
        }
        $mysqli->close();
        ?>
    </div>
</div>

<script>
(function(){
    const selector = document.getElementById('searchSelector');
    const movieComp = document.getElementById('search-movie');
    const actorComp = document.getElementById('search-actor');

    function updateVisibility() {
        if (selector.value === 'movie') {
            movieComp.style.display = '';
            actorComp.style.display = 'none';
        } else {
            movieComp.style.display = 'none';
            actorComp.style.display = '';
        }
    }

    selector.addEventListener('change', function(){
        updateVisibility();
        const url = new URL(window.location.href);
        url.searchParams.set('type', selector.value);
        url.searchParams.delete('action');
        window.location.href = url.toString();
    });

    updateVisibility();
})();
</script>
