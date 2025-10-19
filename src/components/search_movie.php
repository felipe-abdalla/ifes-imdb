<div id="search-movie" class="search-block">
    <form id="form-movie" method="get" action="index.php">
        <input type="hidden" name="page" value="search">
        <input type="hidden" name="type" value="movie">
        <div class="row g-2 mb-2">
            <div class="col-12 col-sm-6">
                <label for="title" class="form-label">Título</label>
                <input type="text" id="title" name="title" class="form-control" value="<?php echo htmlspecialchars($_GET['title'] ?? '', ENT_QUOTES); ?>">
            </div>
            <div class="col-6 col-sm-2">
                <label for="year" class="form-label">Ano</label>
                <input type="text" id="year" name="year" class="form-control" value="<?php echo htmlspecialchars($_GET['year'] ?? '', ENT_QUOTES); ?>">
            </div>
            <div class="col-6 col-sm-2">
                <label for="category" class="form-label">Categoria</label>
                <input type="text" id="category" name="category" class="form-control" value="<?php echo htmlspecialchars($_GET['category'] ?? '', ENT_QUOTES); ?>">
            </div>
            <div class="col-6 col-sm-3">
                <label for="language" class="form-label">Idioma</label>
                <input type="text" id="language" name="language" class="form-control" value="<?php echo htmlspecialchars($_GET['language'] ?? '', ENT_QUOTES); ?>">
            </div>
            <div class="col-6 col-sm-3">
                <label for="rating" class="form-label">Classificação</label>
                <input type="text" id="rating" name="rating" class="form-control" value="<?php echo htmlspecialchars($_GET['rating'] ?? '', ENT_QUOTES); ?>">
            </div>
        </div>

        <div class="d-flex gap-2">
            <button type="submit" name="action" value="filter" class="btn btn-primary">Filtrar</button>
            <a href="index.php?page=search" class="btn btn-secondary">Limpar</a>
        </div>
    </form>
</div>