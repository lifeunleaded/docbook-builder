#!/bin/sh
book=$1
bookfile=$(basename $book)
docname=${bookfile%.xml}
docid=$docname
outputdir=public/$docname

xsltproc --encoding UTF-8 --xinclude --stringparam section.autolabel 0 --stringparam section.label.includes.component.label 0 --stringparam html.stylesheet my.css --stringparam base.dir $outputdir/public/html/ build/docbook-xsl/xhtml-1_1/chunk.xsl $book
cp build/my.css $outputdir/public/html/

cwd=$(pwd)
cd $outputdir/public/
# Create a handy zip of public HTML for download.
zip -r $docname.zip html/
cd $cwd
cp $outputdir/public/$docname.zip output/
echo $docname > buildtmp/docname

# PDF processing.
xsltproc --xinclude --stringparam ulink.show 0 -o buildtmp/$docname.fo build/docbook-xsl/fo/docbook.xsl $book
/fop-1.1/fop buildtmp/$docname.fo -pdf $outputdir/public/$docname.pdf
cp $outputdir/public/$docname.pdf output/


