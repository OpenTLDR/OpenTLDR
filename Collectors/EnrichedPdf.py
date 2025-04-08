
import os
import logging
import io
import pymupdf
import requests

from langchain_text_splitters import RecursiveCharacterTextSplitter

from opentldr import KnowledgeGraph
from opentldr.Domain import Content
from opentldr.ContentEnrichment import TechnicalPaper, Section, TextChunk, Figure

import RepoWriter

class EnrichedPdf:

    pdf_doc:pymupdf.Document = None

    def __init__(self, kg:KnowledgeGraph, content_node:Content, media_cache_path:str,
                 log_level=logging.DEBUG):
        self.kg = kg
        self.content_node = content_node
        self.media_cache_path = media_cache_path
        
        self.log = logging.getLogger("OpenTLDR Collector")
        self.log.setLevel(log_level)

        if not os.path.exists(media_cache_path):
            self.log.info("Creating a directory for media_cache at {}".format(media_cache_path))
            os.makedirs(media_cache_path)

        self.set_text_splitter(RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=20, length_function=len))


    def set_text_splitter(self, splitter):
        self.text_splitter = splitter

    def chunk_text(self, text_in:str) -> list:
        out_chunks = []

        for chunk in self.text_splitter.create_documents([text_in]):
            out_chunks.append(chunk.page_content)
        
        return out_chunks

    def set_log_level(self, level) -> None:
        self.log.setLevel(level)

    def process(self):
        if not hasattr(self.content_node, 'metadata'):
            self.log.warning('Node {uid} does not include any metadata, skipping...')
            return None
        
        if "full_content_pdf" not in self.content_node.metadata:
            self.log.warning('Node {uid} does not include "full_content_pdf" url in metadata, skipping...')
            return None
        
        self.log.debug("Exacting from: {}".format(self.content_node.to_text()))
        self.pdf_doc = self.fetch(self.content_node)
        if self.pdf_doc is not None:
            self.log.debug("Enriching Content from PDF file.")
            section_uids, text_chunk_uids, figure_uids, table_uids, page_images, all_text = self.enrich(self.content_node, self.pdf_doc)
            
            self.log.info('Extracted {pages} pages with {chunks} text chunks, {images} images, and {tables} tables.'.format(
                pages=len(section_uids), chunks=len(text_chunk_uids), images=len(figure_uids),tables=len(table_uids))         )

            self.content_node.metadata["section_uids"]= section_uids
            self.content_node.metadata["text_chunk_uids"]= text_chunk_uids
            self.content_node.metadata["figure_uids"]= figure_uids
            self.content_node.metadata["table_uids"]= table_uids
            self.content_node.metadata["page_images"]= page_images
            self.content_node.metadata["raw_text"] = "\n".join(all_text).replace("\n"," ")

            if self.content_node.text is None or len(self.content_node.text) < 10:
                self.content_node.text = "\n".join(all_text).replace("\n"," ")

            self.content_node.save()


    def fetch (self, content_node:Content):
        pdf_doc = None
        try:
            # attempt to load the file from the media cache
            if "repo_uid" in content_node.metadata:
                media_file = "{}.pdf".format(content_node.metadata["repo_uid"])
                media_path = os.path.join(self.media_cache_path,media_file)
                self.log.debug("Looking for PDF file: {}".format(media_path))
                if os.path.exists(media_path):
                    pdf_doc = pymupdf.open(media_path)
                    #pdf_text = "\n".join([page.get_text() for page in pdf_doc])
                    self.log.info("Found cached media file: {file}".format(file=media_path))
                else:
                    self.log.debug("No PDF file cached.")
        except:
            pass # we are allowed to fail above.

        # pull the media from the url in the content object
        if pdf_doc is None and "full_content_pdf" in content_node.metadata: # didn't load above
            try:
                repo_uid = RepoWriter.non_random_hash(content_node.url)
                media_file = "{}.pdf".format(repo_uid)
                media_path = os.path.join(self.media_cache_path,media_file)

                r = requests.get(content_node.metadata["full_content_pdf"])
                pdf_doc = pymupdf.Document(stream=r.content)

                self.log.info("Saving cached version of {}".format(media_path))
                pdf_doc.save(media_path)

                if self.pdf_doc is None:
                    self.log.warning("Failed to download PDF content.")
                    return None
                
                #self.pdf_text = "\n".join([page.get_text() for page in pdf_doc])
                
                self.log.info("Fetched PDF from URL: {url}".format(url=content_node.url))
            except:
                return None
    
        if pdf_doc is None:
            self.log.error("Failed to get content for node: {}".format(content_node.to_text()))
            return  None
        
        return pdf_doc

    def _enrich_section(self, content_node:Content, section_node:Section):
        pass

    def _enrich_text_chunk(self, content_node:Content, section_node:Section, chunk_node:TextChunk):
        pass

    def _enrich_figure(self, content_node, section_node, figure_node):
        pass

    def _image_to_text(self, image_path:str) -> str:
        return "(an image... of some sort?)"

    def enrich (self, content_node:Content, pdf_doc):
        # Processing document into KG Enrichments
        section_uids = []
        text_chunk_uids = []
        figure_uids = []
        table_uids = []
        page_images = []
        all_text = []

        paper_node = TechnicalPaper(publish_date=content_node.date, title=content_node.title, link=content_node.url)
        paper_node.save()

        paper_node.enriches.connect(content_node)
        # TODO: iterate authors and put into graph as People paper_node.author.connect(...person...)
        chunk_number = 0
        image_number = 0
        page_number = 0

        for page in pdf_doc:
            page_number += 1

            # For PDF pages are the sections
            section_node = Section(title="Page {}".format(page_number))
            pix = page.get_pixmap()
            page_image = os.path.join(self.media_cache_path,"{}_page_{}.png".format(section_node.uid,page_number))
            pix.save(page_image)
            section_node.url = page_image
            section_node.save()
            section_uids.append(section_node.uid)
            page_images.append(page_image)
            paper_node.contains.connect(section_node)
            self._enrich_section(content_node,section_node)
            
            # Process Text Content
            page_text = page.get_text()
            all_text.append(page_text)
            for text_chunk in self.chunk_text(page_text):
                chunk_number += 1
                chunk_node = TextChunk()
                chunk_node.text=text_chunk.replace("\n"," ")
                chunk_node.type="CONCEPT"
                chunk_node.title="Text Chunk {} on Page {}".format(chunk_number,page_number)
                chunk_node.index = chunk_number
                chunk_node.save()
                text_chunk_uids.append(chunk_node.uid)
                chunk_node.mentioned_in.connect(content_node)
                section_node.contains.connect(chunk_node)
                self._enrich_text_chunk(content_node, section_node, chunk_node)

        # Process Figures
        image_list = page.get_images()

        for img in image_list:
            image_number += 1
            figure_node = Figure()
            figure_node.title="Figure {} on Page {}".format(image_number,page_number)
            figure_node.url 
            figure_node.save()
            figure_uids.append(figure_node.uid)
            section_node.contains.connect(figure_node)

            # Extract the image from the PDF
            try:
                xref = img[0]
                pix = pymupdf.Pixmap(pdf_doc,xref)
                image_path = os.path.join(self.media_cache_path,"{}_page_{}_figure_{}.png".format(
                    figure_node.uid,page_number,image_number))
                pix.save(image_path)

                figure_node.url= image_path
                figure_node.description = self._image_to_text(image_path)
                figure_node.save()
                self._enrich_figure(content_node, section_node, figure_node)
            except Exception as e:
                print("Failed to process figure: {}".format(repr(e)))

        # TODO: Process Tables

        return (section_uids, text_chunk_uids, figure_uids, table_uids, page_images, all_text)