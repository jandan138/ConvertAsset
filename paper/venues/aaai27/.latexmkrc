use Cwd 'abs_path';

my $shared = abs_path('../../shared');
for my $name ('TEXINPUTS', 'BIBINPUTS') {
    my $current = $ENV{$name} // '';
    $ENV{$name} = $shared . ':' . $current;
}

$bibtex_use = 2;
$out_dir = 'build';
