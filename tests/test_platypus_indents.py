#Copyright ReportLab Europe Ltd. 2000-2017
#see license.txt for license details
"""Tests for context-dependent indentation
"""
__version__='3.3.0'
from reportlab.lib.testutils import setOutDir,makeSuiteForClasses, outputfile, printLocation
setOutDir(__name__)
import sys, os, random
from operator import truth
import unittest
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus.paraparser import ParaParser
from reportlab.platypus.flowables import Flowable, PageBreak
from reportlab.lib.colors import Color, lightgreen, lightblue
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY
from reportlab.lib.utils import _className
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus.paragraph import Paragraph
from reportlab.platypus.frames import Frame
from reportlab.platypus.doctemplate \
     import PageTemplate, BaseDocTemplate, Indenter, FrameBreak, NextPageTemplate
from reportlab.platypus.tables import TableStyle, Table
from reportlab.platypus.paragraph import *
from reportlab.platypus.paragraph import _getFragWords
from reportlab.platypus.flowables import Spacer
from reportlab.platypus import FrameBG


def myMainPageFrame(canvas, doc):
    "The page frame used for all PDF documents."

    canvas.saveState()

    canvas.rect(2.5*cm, 2.5*cm, 15*cm, 25*cm)
    canvas.setFont('Times-Roman', 12)
    pageNumber = canvas.getPageNumber()
    canvas.drawString(10*cm, cm, str(pageNumber))

    canvas.restoreState()


class MyDocTemplate(BaseDocTemplate):
    _invalidInitArgs = ('pageTemplates',)

    def __init__(self, filename, **kw):
        frame1 = Frame(2.5*cm, 2.5*cm, 15*cm, 25*cm, id='F1')
        self.allowSplitting = 0
        BaseDocTemplate.__init__(self, filename, **kw)
        template1 = PageTemplate('normal', [frame1], myMainPageFrame)

        frame2 = Frame(2.5*cm, 16*cm, 15*cm, 10*cm, id='F2', showBoundary=1)
        frame3 = Frame(2.5*cm, 2.5*cm, 15*cm, 10*cm, id='F3', showBoundary=1)

        template2 = PageTemplate('updown', [frame2, frame3])
        self.addPageTemplates([template1, template2])


class IndentTestCase(unittest.TestCase):
    "Test multi-page splitting of paragraphs (eyeball-test)."

    def test0(self):
        "This makes one long multi-page paragraph."

        # Build story.
        story = []

        styleSheet = getSampleStyleSheet()
        h1 = styleSheet['Heading1']
        h1.spaceBefore = 18
        bt = styleSheet['BodyText']
        bt.spaceBefore = 6

        story.append(Paragraph('Test of context-relative indentation',h1))

        story.append(Spacer(18,18))

        story.append(Indenter(0,0))
        story.append(Paragraph("This should be indented 0 points at each edge. " + ("spam " * 25),bt))
        story.append(Indenter(0,0))

        story.append(Indenter(36,0))
        story.append(Paragraph("This should be indented 36 points at the left. " + ("spam " * 25),bt))
        story.append(Indenter(-36,0))

        story.append(Indenter(0,36))
        story.append(Paragraph("This should be indented 36 points at the right. " + ("spam " * 25),bt))
        story.append(Indenter(0,-36))

        story.append(Indenter(36,36))
        story.append(Paragraph("This should be indented 36 points at each edge. " + ("spam " * 25),bt))
        story.append(Indenter(36,36))
        story.append(Paragraph("This should be indented a FURTHER 36 points at each edge. " + ("spam " * 25),bt))
        story.append(Indenter(-72,-72))

        story.append(Paragraph("This should be back to normal at each edge. " + ("spam " * 25),bt))


        story.append(Indenter(36,36))
        story.append(Paragraph(("""This should be indented 36 points at the left
        and right.  It should run over more than one page and the indent should
        continue on the next page. """ + (random.randint(0,10) * 'x') + ' ') * 20 ,bt))
        story.append(Indenter(-36,-36))

        story.append(NextPageTemplate('updown'))
        story.append(FrameBreak())
        story.append(Paragraph('Another test of context-relative indentation',h1))
        story.append(NextPageTemplate('normal'))  # so NEXT page is different template...
        story.append(Paragraph("""This time we see if the indent level is continued across
            frames...this page has 2 frames, let's see if it carries top to bottom. Then
            onto a totally different template.""",bt))

        story.append(Indenter(0,0))
        story.append(Paragraph("This should be indented 0 points at each edge. " + ("spam " * 25),bt))
        story.append(Indenter(0,0))
        story.append(Indenter(36,72))
        story.append(Paragraph(("""This should be indented 36 points at the left
        and 72 at the right.  It should run over more than one frame and one page, and the indent should
        continue on the next page. """ + (random.randint(0,10) * 'x') + ' ') * 35 ,bt))

        story.append(Indenter(-36,-72))
        story.append(Paragraph("This should be back to normal at each edge. " + ("spam " * 25),bt))
        story.append(PageBreak())

        story.append(PageBreak())
        story.append(Paragraph("Below we should colour the background lightgreen",bt))
        story.append(FrameBG(start=True,color=lightgreen))
        story.append(Paragraph("We should have a light green background here",bt))
        story.append(Paragraph("We should have a light green background here",bt))
        story.append(Paragraph("We should have a light green background here",bt))
        story.append(FrameBG(start=False))

        story.append(PageBreak())
        story.append(Paragraph("Below we should colour the background lightgreen",bt))
        story.append(FrameBG(start="frame",color=lightgreen))
        story.append(Paragraph("We should have a light green background here",bt))

        story.append(PageBreak())
        story.append(Paragraph("Here we should have no background.",bt))

        story.append(PageBreak())
        story.append(FrameBG(start="frame",color=lightblue))
        story.append(Paragraph("We should have a light blue background here and the whole frame should be filled in.",bt))

        story.append(PageBreak())
        story.append(Paragraph("Here we should have no background again.",bt))

        story.append(Paragraph("Below we should colour the background lightgreen",bt))
        story.append(FrameBG(start="frame-permanent",color=lightgreen))
        story.append(Paragraph("We should have a light green background here",bt))

        story.append(PageBreak())
        story.append(Paragraph("Here we should still have a lightgreen background.",bt))

        story.append(PageBreak())
        story.append(FrameBG(start="frame",color=lightblue, left=36, right=36))
        story.append(Paragraph("We should have a lighgreen/lightblue background.",bt))

        story.append(PageBreak())
        story.append(Paragraph("Here we should have only light green background.",bt))


        doc = MyDocTemplate(outputfile('test_platypus_indents.pdf'))
        doc.multiBuild(story)


#noruntests
def makeSuite():
    return makeSuiteForClasses(IndentTestCase)


#noruntests
if __name__ == "__main__":
    unittest.TextTestRunner().run(makeSuite())
    printLocation()
