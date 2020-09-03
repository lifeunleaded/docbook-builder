# docbook-builder
This is a very slimmed-down version of automatic building of DocBook content. To use this, the contents can be cloned and pushed to a repo on a GitLab instance with CI using docker runners enabled. Put your XSLT 1.0 templates in the build/ directory and name it docbook-xsl, change the contents in the testbook/book.xml example, and push, and the CI should<tm> build a PDF and HTML bundle and deliver as build artifacts.
  
There are a lot of mechanisms that can be enabled in addition (I use profiling and olink databases, and also handle DITA content), but that is best handled as local adaptations, mainly in the build/builder.sh script.
