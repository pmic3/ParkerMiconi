import components.simplereader.SimpleReader;
import components.simplereader.SimpleReader1L;
import components.simplewriter.SimpleWriter;
import components.simplewriter.SimpleWriter1L;
import components.xmltree.XMLTree;
import components.xmltree.XMLTree1;

/**
 * Program to convert an XML RSS (version 2.0) containing a list of feeds from a
 * given URL into the corresponding HTML output file with the ability to
 * navigate to each feed.
 *
 *
 * @author Parker Miconi
 *
 */
public final class RSSAggregator {

    /**
     * Private constructor so this utility class cannot be instantiated.
     */
    private RSSAggregator() {
    }

    /**
     * Processes one XML RSS (version 2.0) feed from a given URL converting it
     * into the corresponding HTML output file.
     *
     * @param url
     *            the URL of the RSS feed
     * @param fileName
     *            the name of the HTML output file
     * @param out
     *            the output stream to report progress or errors
     * @updates out.content
     * @requires out.is_open
     * @ensures <pre>
     * [reads RSS feed from url, saves HTML document with table of news items
     *   to fileName, appends to out.content any needed messages]
     * </pre>
     */
    private static void processFeed(String url, String fileName, SimpleWriter out) {
        /* Read RSS feed into XMLTree */
        XMLTree rss = new XMLTree1(url);

        /* Check if the feed is RSS 2.0 */
        if (!rss.label().equals("rss") || !rss.hasAttribute("version")
                || !rss.attributeValue("version").equals("2.0")) {
            out.println("Invalid RSS 2.0 feed at URL: " + url);
        } else {
            /* Open output file */
            SimpleWriter fileOut = new SimpleWriter1L(fileName);

            /* Find the <channel> element */
            int channelIndex = getChildElement(rss, "channel");
            XMLTree channel = rss.child(channelIndex);

            /* Output the header */
            outputHeader(channel, fileOut);

            /* Process each <item> element */
            for (int i = 0; i < channel.numberOfChildren(); i++) {
                XMLTree child = channel.child(i);
                if (child.isTag() && child.label().equals("item")) {
                    processItem(child, fileOut);
                }
            }

            /* Output the footer */
            outputFooter(fileOut);

            /* Close the output file */
            fileOut.close();

            out.println("Generated HTML file: " + fileName);
        }
    }

    /**
     * Outputs the "opening" tags in the generated HTML file.
     *
     * @param channel
     *            the channel element XMLTree
     * @param out
     *            the output stream
     * @updates out.content
     * @requires [the root of channel is a <channel> tag] and out.is_open
     * @ensures out.content = #out.content * [the HTML "opening" tags]
     */
    private static void outputHeader(XMLTree channel, SimpleWriter out) {
        /* Get the title */
        int titleIndex = getChildElement(channel, "title");
        String title = "No title";

        if (channel.child(titleIndex).numberOfChildren() > 0) {
            title = channel.child(titleIndex).child(0).label();
        }

        /* Get the link */
        int linkIndex = getChildElement(channel, "link");
        String link = "";

        if (channel.child(linkIndex).numberOfChildren() > 0) {
            link = channel.child(linkIndex).child(0).label();
        }

        /* Get the description */
        int descIndex = getChildElement(channel, "description");
        String description = "No description";

        if (channel.child(descIndex).numberOfChildren() > 0) {
            description = channel.child(descIndex).child(0).label();
        }

        /* Output HTML header */
        out.println("<html>");
        out.println("<head>");
        out.println("  <title>" + title + "</title>");
        out.println("</head>");
        out.println("<body>");
        out.println("  <h1><a href=\"" + link + "\">" + title + "</a></h1>");
        out.println("  <p>" + description + "</p>");
        out.println("  <table border=\"1\">");
        out.println("    <tr>");
        out.println("      <th>Date</th>");
        out.println("      <th>Source</th>");
        out.println("      <th>News</th>");
        out.println("    </tr>");
    }

    /**
     * Outputs the "closing" tags in the generated HTML file.
     *
     * @param out
     *            the output stream
     * @updates out.contents
     * @requires out.is_open
     * @ensures out.content = #out.content * [the HTML "closing" tags]
     */
    private static void outputFooter(SimpleWriter out) {
        out.println("  </table>");
        out.println("</body>");
        out.println("</html>");
    }

    /**
     * Finds the first occurrence of the given tag among the children of the
     * given {@code XMLTree} and return its index; returns -1 if not found.
     *
     * @param xml
     *            the {@code XMLTree} to search
     * @param tag
     *            the tag to look for
     * @return the index of the first child of type tag of the {@code XMLTree}
     *         or -1 if not found
     * @requires [the label of the root of xml is a tag]
     * @ensures <pre>
     * getChildElement =
     *  [the index of the first child of type tag of the {@code XMLTree} or
     *   -1 if not found]
     * </pre>
     */
    private static int getChildElement(XMLTree xml, String tag) {
        int result = -1;
        int i = 0;
        while (i < xml.numberOfChildren() && result == -1) {
            XMLTree child = xml.child(i);
            if (child.isTag() && child.label().equals(tag)) {
                result = i;
            }
            i++;
        }
        return result;
    }

    /**
     * Processes one news item and outputs one table row.
     *
     * @param item
     *            the news item
     * @param out
     *            the output stream
     * @updates out.content
     * @requires [the label of the root of item is an <item> tag] and
     *           out.is_open
     * @ensures <pre>
     * out.content = #out.content *
     *   [an HTML table row with publication date, source, and title of news item]
     * </pre>
     */
    private static void processItem(XMLTree item, SimpleWriter out) {
        out.println("    <tr>");

        /* Process publication date */
        int pubDateIndex = getChildElement(item, "pubDate");
        String pubDate = "No date available";
        if (pubDateIndex != -1) {
            pubDate = item.child(pubDateIndex).child(0).label();
        }
        out.println("      <td>" + pubDate + "</td>");

        /* Process source */
        int sourceIndex = getChildElement(item, "source");
        String sourceName = "No source available";
        String sourceURL = "";
        if (sourceIndex != -1) {
            XMLTree source = item.child(sourceIndex);
            if (source.hasAttribute("url")) {
                sourceURL = source.attributeValue("url");
            }
            if (source.numberOfChildren() > 0) {
                sourceName = source.child(0).label();
            }
            if (!sourceURL.isEmpty()) {
                sourceName = "<a href=\"" + sourceURL + "\">" + sourceName + "</a>";
            }
        }
        out.println("      <td>" + sourceName + "</td>");

        /* Process title or description */
        int titleIndex = getChildElement(item, "title");
        int descIndex = getChildElement(item, "description");
        int linkIndex = getChildElement(item, "link");

        String newsTitle = "No title available";
        if (titleIndex != -1) {
            if (item.child(titleIndex).numberOfChildren() > 0) {
                newsTitle = item.child(titleIndex).child(0).label();
            }
        } else if (descIndex != -1) {
            if (item.child(descIndex).numberOfChildren() > 0) {
                newsTitle = item.child(descIndex).child(0).label();
            }
        }

        String newsLink = "";
        if (linkIndex != -1) {
            if (item.child(linkIndex).numberOfChildren() > 0) {
                newsLink = item.child(linkIndex).child(0).label();
            }
        }

        if (!newsLink.isEmpty()) {
            newsTitle = "<a href=\"" + newsLink + "\">" + newsTitle + "</a>";
        }

        out.println("      <td>" + newsTitle + "</td>");

        out.println("    </tr>");
    }

    /**
     * Main method.
     *
     * @param args
     *            the command line arguments; unused here
     */
    public static void main(String[] args) {
        SimpleReader in = new SimpleReader1L();
        SimpleWriter out = new SimpleWriter1L();

        /*
         * Prompt user for the name of the XML file containing the list of feeds
         */
        out.print("Enter the name of the XML file containing the list of feeds: ");
        String feedsFile = in.nextLine();

        /* Prompt user for the name of the index HTML file */
        out.print("Enter the name of the index HTML file to generate: ");
        String indexFileName = in.nextLine();

        /* Read the feeds XML file into XMLTree */
        XMLTree feeds = new XMLTree1(feedsFile);

        /* Get the title attribute from <feeds> */
        String indexTitle = "RSS Aggregator";
        if (feeds.hasAttribute("title")) {
            indexTitle = feeds.attributeValue("title");
        }

        /* Open the index HTML file */
        SimpleWriter indexOut = new SimpleWriter1L(indexFileName);

        /* Output index HTML header */
        indexOut.println("<html>");
        indexOut.println("<head>");
        indexOut.println("  <title>" + indexTitle + "</title>");
        indexOut.println("</head>");
        indexOut.println("<body>");
        indexOut.println("  <h1>" + indexTitle + "</h1>");
        indexOut.println("  <ul>");

        /* Process each <feed> element */
        for (int i = 0; i < feeds.numberOfChildren(); i++) {
            XMLTree feed = feeds.child(i);
            if (feed.label().equals("feed")) {
                String url = "";
                String name = "";
                String fileName = "";

                if (feed.hasAttribute("url")) {
                    url = feed.attributeValue("url");
                }
                if (feed.hasAttribute("name")) {
                    name = feed.attributeValue("name");
                }
                if (feed.hasAttribute("file")) {
                    fileName = feed.attributeValue("file");
                }

                if (!url.isEmpty() && !name.isEmpty() && !fileName.isEmpty()) {
                    /* Process the feed */
                    processFeed(url, fileName, out);

                    /* Add link to the feed HTML file in the index page */
                    indexOut.println(
                            "    <li><a href=\"" + fileName + "\">" + name + "</a></li>");
                } else {
                    out.println("Feed element missing required attributes at index " + i);
                }
            }
        }

        /* Output index HTML footer */
        indexOut.println("  </ul>");
        indexOut.println("</body>");
        indexOut.println("</html>");

        /* Close the index HTML file */
        indexOut.close();

        in.close();
        out.close();
    }

}
