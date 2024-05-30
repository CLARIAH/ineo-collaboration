<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:math="http://www.w3.org/2005/xpath-functions/math"
    xmlns:cmd="http://www.clarin.eu/cmd/"
    xmlns:js="http://www.w3.org/2005/xpath-functions"
    xmlns:cl="https://www.clariah.nl/"
    exclude-result-prefixes="xs math cmd js"
    version="3.0">
    
    <xsl:output method="text" encoding="UTF-8"/>
    
    <!--<xsl:param name="js-uri" select="()"/>-->
    <xsl:param name="js-uri" select="'file:/Users/menzowi/Documents/Projects/CLARIAH/INEO/HI/RUC/hi_bgb.json'"/>
    <xsl:param name="js-doc" select="unparsed-text($js-uri)"/>
    <xsl:param name="js-xml" select="js:json-to-xml($js-doc)"/>
    
    <xsl:param name="type" select="'Data'"/>
    
    <xsl:param name="vocabs" select="'file:/Users/menzowi/Documents/Projects/CLARIAH/INEO/HI/vocabs/'"/>
    <xsl:param name="vocabs-ext" select="'.json'"/>
    
    <xsl:function name="cl:lookupLink" as="xs:string?">
        <xsl:param name="val"/>
        <xsl:param name="vocab"/>
        <xsl:variable name="vocab-xml" select="js:json-to-xml(unparsed-text(concat($vocabs,$vocab,$vocabs-ext)))"/>
        <xsl:sequence select="$vocab-xml//js:map[lower-case(normalize-space(js:string[@key='title']))=lower-case(normalize-space($val))]/js:string[@key='link']"/>
    </xsl:function>
    
    <xsl:function name="cl:lookupIndex" as="xs:string?">
        <xsl:param name="val"/>
        <xsl:param name="vocab"/>
        <xsl:variable name="vocab-xml" select="js:json-to-xml(unparsed-text(concat($vocabs,$vocab,$vocabs-ext)))"/>
        <xsl:sequence select="$vocab-xml//js:map[lower-case(normalize-space(js:string[@key='title']))=lower-case(normalize-space($val))]/concat(js:string[@key='index'],' ',js:string[@key='title'])"/>
    </xsl:function>
  
    <xsl:function name="cl:lookupTitle" as="xs:string?">
        <xsl:param name="val"/>
        <xsl:param name="vocab"/>
        <xsl:variable name="vocab-xml" select="js:json-to-xml(unparsed-text(concat($vocabs,$vocab,$vocabs-ext)))"/>
        <xsl:sequence select="$vocab-xml//js:map[lower-case(normalize-space(js:string[@key='title']))=lower-case(normalize-space($val))]/js:string[@key='title']"/>
    </xsl:function>
    
    <xsl:template match="/">
        <xsl:variable name="id" select="normalize-space($js-xml//js:string[@key='identifier'])"/>
        <xsl:choose>
            <xsl:when test="$id=''">
                <xsl:message>?DBG: no RUC (identifier)</xsl:message>
            </xsl:when>
            <xsl:when test="(//cmd:Components/cmd:HI/cmd:ID!=$id)">
                <xsl:message terminate="yes" expand-text="yes">!ERR: CMD ID[{$id}] and RUC identifier[{//cmd:Components/cmd:HI/cmd:ID}] don't match!</xsl:message>
            </xsl:when>
        </xsl:choose>
        <xsl:variable name="ineo">
            <js:array>
                <js:map>
                    <js:string key="operation">create</js:string>
                    <js:map key="document">
                        <js:string key="id">
                            <xsl:value-of select="//cmd:Components/cmd:HI/cmd:ID"/>
                        </js:string>
                        <js:string key="title">
                            <xsl:value-of select="//cmd:Components/cmd:HI/cmd:Dataset/(cmd:title[@xml:lang='en'],cmd:title[normalize-space(@xml:lang)=''])[1]"/>
                        </js:string>
                        <js:string key="intro">
                            <xsl:value-of select="//cmd:Components/cmd:HI/cmd:Dataset/(cmd:description[@xml:lang='en'],cmd:description[normalize-space(@xml:lang)=''])[1]"/>
                        </js:string>
                        <js:string key="publishedAt">
                            <xsl:value-of select="//cmd:Components/cmd:HI/cmd:Dataset/cmd:issued"/>
                        </js:string>
                        <js:map key="media">
                            <!--<js:string key="thumbnail">https://picsum.photos/800/600.webp</js:string>
                            <js:array key="slider">
                                <js:string>https://picsum.photos/800/600.webp</js:string>
                                <js:string>https://vimeo.com/538016781</js:string>
                                <js:string>https://youtu.be/INUHCQST7CU</js:string>
                            </js:array>-->
                        </js:map>
                        <js:map key="tabs">
                            <js:map key="overview">
                                <js:string key="body">
                                    <xsl:value-of select="$js-xml//js:string[@key='Overview']"/>
                                </js:string>
                                <!--<js:string key="bodyMore">null</js:string>-->
                            </js:map>
                            <js:map key="learn">
                                <js:string key="body">
                                    <xsl:value-of select="$js-xml//js:string[@key='Learn']"/>
                                </js:string>
                                <js:string key="bodyMore">null</js:string>
                            </js:map>
                            <js:map key="mentions">
                                <js:string key="body">
                                    <xsl:value-of select="$js-xml//js:string[@key='Mentions']"/>
                                </js:string>
                                <js:string key="bodyMore">null</js:string>
                            </js:map>
                            <js:map key="metadata">
                                <!--<js:string key="body">markdown</js:string>-->
                            </js:map>
                        </js:map>
                        <js:map key="properties">
                            <js:string key="link">
                                <xsl:value-of select="//cmd:Components/cmd:HI/cmd:Dataset/cmd:landingPage"/>
                            </js:string>
                            <js:string key="intro">
                                <xsl:value-of select="//cmd:Components/cmd:HI/cmd:Dataset/(cmd:description[@xml:lang='en'],cmd:description[normalize-space(@xml:lang)=''])[1]"/>
                            </js:string>
                            <js:array key="resourceTypes">
                                    <js:string>
                                        <xsl:value-of select="$type"/>
                                    </js:string>
                            </js:array>
                            <js:array key="researchActivities">
                                <xsl:for-each select="//cmd:Components/cmd:HI/cmd:INEO/cmd:researchActivity[normalize-space(.)!='']">
                                    <!--<js:string>https://vocabs.dariah.eu/tadirah/namingConvention</js:string>-->
                                    <js:string>
                                        <xsl:value-of select="normalize-space(cl:lookupLink(.,'researchActivities'))"/>
                                    </js:string>
                                </xsl:for-each>
                            </js:array>
                            <js:array key="researchDomains">
                                <xsl:for-each select="//cmd:Components/cmd:HI/cmd:INEO/cmd:researchDomain[normalize-space(.)!='']">
                                    <!--<js:string>https://w3id.org/nwo-research-fields#HistoryofScience</js:string>-->
                                    <js:string>
                                        <xsl:value-of select="normalize-space(cl:lookupLink(.,'researchDomains'))"/>
                                    </js:string>
                                </xsl:for-each>
                            </js:array>
                            <js:array key="informationTypes">
                                <xsl:for-each select="//cmd:Components/cmd:HI/cmd:INEO/cmd:informationType[normalize-space(.)!='']">
                                    <!--<js:string>1.22 Statistics</js:string>
                                    <js:string>2.8 Numeric data</js:string>-->
                                    <js:string>
                                        <xsl:value-of select="normalize-space(cl:lookupIndex(.,'informationTypes'))"/>
                                    </js:string>
                                </xsl:for-each>
                            </js:array>
                            <js:array key="mediaTypes">
                                <xsl:for-each select="//cmd:Components/cmd:HI/cmd:INEO/cmd:mediaType[normalize-space(.)!='']">
                                    <!--<js:string>1.997 vnd.svd</js:string>-->
                                    <js:string>
                                        <xsl:value-of select="normalize-space(cl:lookupIndex(.,'mediaTypes'))"/>
                                    </js:string>
                                </xsl:for-each>
                            </js:array>
                            <js:array key="status">
                                <xsl:for-each select="//cmd:Components/cmd:HI/cmd:INEO/cmd:status[normalize-space(.)!='']">
                                    <js:string>
                                        <xsl:value-of select="normalize-space(cl:lookupTitle(.,'status'))"/>
                                    </js:string>
                                </xsl:for-each>
                            </js:array>
                            <js:array key="languages">
                                <xsl:for-each select="//cmd:Components/cmd:HI/cmd:INEO/cmd:language[normalize-space(.)!='']">
                                    <js:string>
                                        <xsl:value-of select="normalize-space(cl:lookupIndex(.,'languages'))"/>
                                    </js:string>
                                </xsl:for-each>
                            </js:array>
                            <js:array key="access">
                                <xsl:for-each select="//cmd:Components/cmd:HI/cmd:INEO/cmd:Access[normalize-space(.)!='']">
                                    <js:map>
                                        <js:string key="title">
                                            <xsl:value-of select="."/>
                                        </js:string>
                                        <js:string key="link">null</js:string>
                                    </js:map>
                                </xsl:for-each>
                            </js:array>
                            <js:array key="versions">
                                <xsl:for-each select="//cmd:Components/cmd:HI/cmd:INEO/cmd:Version[normalize-space(.)!='']">
                                    <js:map>
                                        <js:string key="title">
                                            <xsl:value-of select="."/>
                                        </js:string>
                                        <js:string key="link">null</js:string>
                                    </js:map>
                                </xsl:for-each>
                            </js:array>
                            <js:array key="programmingLanguages">
                                <!--<js:map>
                                    <js:string key="title">string</js:string>
                                    <js:string key="link">url</js:string>
                                </js:map>-->
                            </js:array>
                            <js:array key="standards">
                                <!--<js:map>
                                    <js:string key="title">string</js:string>
                                    <js:string key="link">url</js:string>
                                </js:map>-->
                            </js:array>
                            <js:array key="provenance">
                                <xsl:for-each select="//cmd:Components/cmd:HI/cmd:INEO/cmd:provenance[normalize-space(.)!='']">
                                    <js:map>
                                        <js:string key="title">
                                            <xsl:value-of select="."/>
                                        </js:string>
                                        <js:string key="link">null</js:string>
                                    </js:map>
                                </xsl:for-each>
                            </js:array>
                            <js:array key="sourceCodeLocation">
                                <!--<js:map>
                                    <js:string key="title">string</js:string>
                                    <js:string key="link">url</js:string>
                                </js:map>-->
                            </js:array>
                            <js:array key="learn">
                                <!--<js:map>
                                    <js:string key="title">string</js:string>
                                    <js:string key="link">url</js:string>
                                </js:map>-->
                            </js:array>
                            <js:array key="community">
                                <xsl:for-each select="//cmd:Components/cmd:HI/cmd:INEO/cmd:community[normalize-space(.)!='']">
                                    <js:map>
                                        <js:string key="title">
                                            <xsl:value-of select="."/>
                                        </js:string>
                                        <js:string key="link">null</js:string>
                                    </js:map>
                                </xsl:for-each>
                            </js:array>
                            <js:array key="resourceHost">
                                <xsl:for-each select="//cmd:Components/cmd:HI/cmd:INEO/cmd:resourceHost[normalize-space(.)!='']">
                                    <js:map>
                                        <js:string key="title">
                                            <xsl:value-of select="."/>
                                        </js:string>
                                        <js:string key="link">
                                            <xsl:value-of select="."/>
                                        </js:string>
                                    </js:map>
                                </xsl:for-each>
                            </js:array>
                            <js:array key="resourceOwner">
                                <xsl:for-each select="//cmd:Components/cmd:HI/cmd:INEO/cmd:resourceOwner[normalize-space(.)!='']">
                                    <js:map>
                                        <js:string key="title">
                                            <xsl:value-of select="."/>
                                        </js:string>
                                        <js:string key="link">
                                            <xsl:value-of select="."/>
                                        </js:string>
                                    </js:map>
                                </xsl:for-each>
                            </js:array>
                            <js:array key="development">
                                <!--<js:map>
                                    <js:string key="title">string</js:string>
                                    <js:string key="link">url</js:string>
                                </js:map>-->
                            </js:array>
                            <js:array key="funding">
                                <!--<js:map>
                                    <js:string key="title">string</js:string>
                                    <js:string key="link">url</js:string>
                                </js:map>-->
                            </js:array>
                            <js:array key="generalContact">
                                <xsl:for-each select="//cmd:Components/cmd:HI/cmd:INEO/cmd:contactForGeneralQuestions[normalize-space(.)!='']">
                                    <js:map>
                                        <js:string key="title">
                                            <xsl:value-of select="."/>
                                        </js:string>
                                        <js:string key="link">
                                            <xsl:value-of select="."/>
                                        </js:string>
                                    </js:map>
                                </xsl:for-each>
                            </js:array>
                            <js:array key="researchContact">
                                <xsl:for-each select="//cmd:Components/cmd:HI/cmd:INEO/cmd:contactForResearchQuestions[normalize-space(.)!='']">
                                    <js:map>
                                        <js:string key="title">
                                            <xsl:value-of select="."/>
                                        </js:string>
                                        <js:string key="link">
                                            <xsl:value-of select="."/>
                                        </js:string>
                                    </js:map>
                                </xsl:for-each>
                            </js:array>
                            <js:array key="problemContact">
                                <xsl:for-each select="//cmd:Components/cmd:HI/cmd:INEO/cmd:contactForReportingAProblem[normalize-space(.)!='']">
                                    <js:map>
                                        <js:string key="title">
                                            <xsl:value-of select="."/>
                                        </js:string>
                                        <js:string key="link">
                                            <xsl:value-of select="."/>
                                        </js:string>
                                    </js:map>
                                </xsl:for-each>
                            </js:array>
                        </js:map>
                    </js:map>
                </js:map>
            </js:array>
        </xsl:variable>
       <!-- <xsl:copy-of select="$ineo"/>-->
        <xsl:value-of select="js:xml-to-json($ineo)"/>
    </xsl:template>
    
</xsl:stylesheet>