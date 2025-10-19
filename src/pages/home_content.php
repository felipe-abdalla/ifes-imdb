<?php
// AConfig
$dbHost = 'localhost';
$dbUser = 'root';
$dbPass = 'dx66ksdc';
$dbName = 'imdb';

$mysqli = new mysqli($dbHost, $dbUser, $dbPass, $dbName);
if ($mysqli->connect_errno) {
    echo '<div class="container mt-4"><div class="alert alert-danger">Erro ao conectar ao banco de dados.</div></div>';
    return;
}

// Query: top 10 por nota (filmes com nota NULL ficam por último)
$sql = "
    SELECT f.titulo, f.ano, c.descricao AS categoria, f.nota
    FROM Filme f
    LEFT JOIN Categoria c ON f.Categoria = c.id
    ORDER BY f.nota DESC, f.titulo ASC
    LIMIT 10
";
if (!$result = $mysqli->query($sql)) {
    echo '<div class="container mt-4"><div class="alert alert-danger">Erro na consulta ao banco.</div></div>';
    $mysqli->close();
    return;
}

$movies = $result->fetch_all(MYSQLI_ASSOC);
$result->free();
$mysqli->close();
?>

<div class="title-best-rated">
    <h2>TOP 10 FILMES POR AVALIAÇÃO DOS USUÁRIOS</h2>
</div>
<div class="container-best-rated container text-center">
    <div class="row fw-bold mt-2">
        <div class="col-1">
            <p>#</p`>
        </div>
        <div class="col-5 text-start">
            <p>TÍTULO</p>
        </div>
        <div class="col-2">
            <p>ANO</p>
        </div>
        <div class="col-2">
            <p>CATEGORIA</p>
        </div>
        <div class="col-2">
            <p>NOTA</p>
        </div>
    </div>

    <?php if (empty($movies)): ?>
            <div class="row">
                <div class="col">
                    <p>Nenhum filme encontrado.</p>
                </div>
            </div>
        <?php else: ?>
            <?php $pos = 1; ?>
            <?php foreach ($movies as $m): ?>
                <div class="row align-items-center py-2">
                    <hr class="mb-3">
                    <div class="col-1">
                        <span><?php echo (int)$pos; ?></span>
                    </div>
                    <div class="col-5 text-start">
                        <span><?php echo htmlspecialchars($m['titulo'] ?? 'N/A', ENT_QUOTES, 'UTF-8'); ?></span>
                    </div>
                    <div class="col-2">
                        <span><?php echo htmlspecialchars($m['ano'] ?? 'N/A', ENT_QUOTES, 'UTF-8'); ?></span>
                    </div>
                    <div class="col-2">
                        <span><?php echo htmlspecialchars($m['categoria'] ?? 'N/A', ENT_QUOTES, 'UTF-8'); ?></span>
                    </div>
                    <div class="col-2">
                        <span><?php echo is_numeric($m['nota']) ? number_format((float)$m['nota'], 1, ',', '.') : 'N/A'; ?></span>
                    </div>
                </div>
                <?php $pos++; ?>
            <?php endforeach; ?>
        <?php endif; ?>
</div>