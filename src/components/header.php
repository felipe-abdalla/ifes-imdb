<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.8/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-sRIl4kxILFvY47J16cr9ZwB07vP4J8+LH7qKQnuqkuIAvNWLzeN8tE5YBujZqJLB" crossorigin="anonymous">
    <link rel="stylesheet" href="../css/style.css">
    <title>IFES Movie Database</title>
</head>
<body>
    <header>
        <div class="title d-flex justify-content-center align-items-center">
            <h1 class="text-center fs-1">IFES Movie Database</h1>
        </div>

        <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
            <div class="container-fluid">
                <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
                    <span class="navbar-toggler-icon"></span>
                </button>
                <div class="collapse navbar-collapse" id="navbarNav">
                    <ul class="navbar-nav">
                        <li class="nav-item">
                            <a class="nav-link <?php echo ($page ?? '') === 'home' ? 'active' : ''; ?>" href="index.php?page=home">Página Inicial</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link <?php echo ($page ?? '') === 'listar' ? 'active' : ''; ?>" href="index.php?page=list">Lista de Filmes</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link <?php echo ($page ?? '') === 'busca' ? 'active' : ''; ?>" href="index.php?page=search">Busca</a>
                        </li>
                    </ul>
                </div>
            </div>
        </nav>
    </header>