<?php
$page = $_GET['page'] ?? 'home';

include './src/components/header.php';
?>

<section class="content">
<?php
if ($page === 'list') {
    include './src/pages/list_content.php';
} elseif ($page === 'search') {
    include './src/pages/search_content.php';
} else {
    include './src/pages/home_content.php';
}
?>
</section>

<?php
include './src/components/footer.php';
?>