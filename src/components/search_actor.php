<div id="search-actor" class="search-block">
    <form id="form-actor" method="get" action="index.php">
        <input type="hidden" name="page" value="search">
        <input type="hidden" name="type" value="actor">
        <div class="row g-2 mb-2">
            <div class="col-12 col-sm-4">
                <label for="actor_name" class="form-label">Nome</label>
                <input type="text" id="actor_name" name="actor_name" class="form-control" value="<?php echo htmlspecialchars($_GET['actor_name'] ?? '', ENT_QUOTES); ?>">
            </div>
            <div class="col-12 col-sm-4">
                <label for="actor_lastname" class="form-label">Sobrenome</label>
                <input type="text" id="actor_lastname" name="actor_lastname" class="form-control" value="<?php echo htmlspecialchars($_GET['actor_lastname'] ?? '', ENT_QUOTES); ?>">
            </div>
            <div class="col-12 col-sm-4">
                <label for="actor_nationality" class="form-label">Nacionalidade</label>
                <input type="text" id="actor_nationality" name="actor_nationality" class="form-control" value="<?php echo htmlspecialchars($_GET['actor_nationality'] ?? '', ENT_QUOTES); ?>">
            </div>
        </div>

        <div class="d-flex gap-2">
            <button type="submit" name="action" value="filter" class="btn btn-primary">Filtrar</button>
            <a href="index.php?page=search" class="btn btn-secondary">Limpar</a>
        </div>
    </form>
</div>