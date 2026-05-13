use Cwd 'abs_path';

sub ensure_path {
    my ($name, $path) = @_;
    my $current = $ENV{$name} // '';
    $ENV{$name} = $path . ':' . $current;
}

my $shared = abs_path('../../shared');
ensure_path('TEXINPUTS', $shared);
ensure_path('BIBINPUTS', $shared);

$bibtex_use = 2;
$out_dir = 'build';
