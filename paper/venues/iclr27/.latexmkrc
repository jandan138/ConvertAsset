$pdf_mode = 1;
$pdflatex = 'pdflatex -interaction=nonstopmode -halt-on-error %O %S';
use Cwd qw(abs_path);
$ENV{'BIBINPUTS'} = abs_path('.') . ':' . abs_path('../../shared') . ':' . ($ENV{'BIBINPUTS'} // '');
