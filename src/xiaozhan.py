import requests
import json
import lxml
from lxml import etree
import re
import os

with open("../../nlp_lexicon_crawler/notebooks/prefix-176.json", "r", encoding="utf-8") as f:
    Prefixs = json.load(f)

with open("../../nlp_lexicon_crawler/notebooks/suffix-248.json", "r", encoding="utf-8") as f:
    Suffixs = json.load(f)

with open("../../nlp_lexicon_crawler/notebooks/root-609.json", "r", encoding="utf-8") as f:
    Roots = json.load(f)


class XiaozhanCrawler(object):

    def __init__(self):
        self.source = "xiaozhan"
        self.url = "http://top.zhan.com/cihui/%s-%s.html"
        self.countryCh2En = {"美": "US", "英": "UK"}
        self.items = ["PhoneticSymbols", "Paraphrases", "Inflections", "Collocations", "Derivatives", "WordFormations",
                      "RootAffixs", "SynonymAntonyms"]
        self.dictPath = "../dicts/xiaozhan/"
        if not os.path.exists(self.dictPath):
            os.makedirs(self.dictPath)

    def get_infos(self, lexicon):
        """
        提取词汇信息.
        """
        lexicon = lexicon.strip()
        if lexicon in os.listdir(self.dictPath):
            return self.read_infos(lexicon)
        else:
            if len(lexicon.split()) > 1:
                lexiconType = "Phrase"
            else:
                lexiconType = "Word"
            result = {"Lexicon": lexicon, "type": lexiconType, "source": self.source}
            try:
                url = self.url % ("toefl", lexicon)
                html = etree.parse(url, etree.HTMLParser(encoding="utf-8"))
                for k in self.items:
                    try:
                        result[k] = eval("self.get_%s(html, lexicon)" % k)
                    except Exception as e:
                        print("Error: {}, {}".format(lexicon, repr(e)))
                # 保存词汇信息
                if lexicon not in result["Inflections"].values():
                    isSave = False
                    for k in self.items:
                        if k in result.keys() and result[k]:
                            isSave = True
                            break
                    if isSave:
                        self.save_infos(lexicon, result)
                else:
                    print("Warning: {} in Inflections: {}".format(lexicon, result["Inflections"]))
            except Exception:
                pass
            return result

    def get_phonetic_symbol(self, html):
        """
        音标提取.
        """

        ps = html.xpath("//div[@class='cssVocWordVideo jsControlAudio']/span")
        outs = []
        if len(ps) >= 2:
            country = ps[0].text.strip()
            assert ps[1].text.strip()[0] == "[" and ps[1].text.strip()[-1] == "]"
            name = "/" + ps[1].text.strip()[1:-1] + "/"
            out = {"country": self.countryCh2En[country], "audioUrl": "", "name": name, "source": self.source}
            outs.append(out)
        return outs

    def get_PhoneticSymbols(self, html, lexicon, name="toefl"):
        """
        美英音标提取.
        """
        outs = []
        try:
            # IELTS
            url = self.url % ("ielts", lexicon)
            html = etree.parse(url, etree.HTMLParser(encoding="utf-8"))
            outs += self.get_phonetic_symbol(html)

            # TOEFL
            url = self.url % ("toefl", lexicon)
            html = etree.parse(url, etree.HTMLParser(encoding="utf-8"))
            outs += self.get_phonetic_symbol(html)
        except Exception:
            pass
        return outs

    def get_Paraphrases(self, html, lexicon, name="toefl"):
        """
        释义、例句信息提取.
        """
        paraphrases = []
        # 常考释义
        try:
            paras = html.xpath("//ul[@class='cssVocPartBox']/li/text()")
            for para in paras:
                para = para.split('","')
                if para:
                    para = para[0].split(".", 1)
                    if len(para) == 2:
                        pos = para[0] + "."
                        parapch = para[1].strip()
                        sents = html.xpath("//div[@class='cssVocExSentence']")
                        sentences = []
                        for s in sents:
                            e = s.xpath("string(./div/p[@class='cssVocExEnglish'])").strip()
                            c = s.xpath("string(./p[@class='cssVocExChinese'])").strip()
                            value = {"english": e, "chinese": c, "source": self.source + "-usual", "audioUrlUS": "",
                                     "audioUrlUK": ""}
                            sentences.append(value)
                        paraphrase = {"pos": pos, "english": "", "chinese": parapch, "Sentences": sentences,
                                      "source": self.source, "frequency": 1.0}

                        paraphrases.append(paraphrase)
        except Exception:
            pass
        # 英汉双解
        ps = html.xpath("//li[@class='cssVocCont jsVocCont active']/ul/li")
        for p in ps:
            try:
                # 获取词性、释义信息
                paras = p.xpath("./div/p[@class='cssVocTotoleChinese']/text()")[0]
                para = paras.split(".", 1)
                if len(para) != 2:
                    continue
                pos = para[0] + "."
                parapch = para[1].strip()

                # 获取简明例句
                sentInfos = p.xpath("./div/div/div[1]/descendant::p[@class='cssVocExEnglish']")
                jianmingSentEns = [i.xpath('string(.)').strip() for i in sentInfos]
                sentInfos = p.xpath("./div/div/div[1]/descendant::p[@class='cssVocExChinese']")
                jianmingSentChs = [i.xpath('string(.)').strip() for i in sentInfos]

                # 获取情景例句
                sentInfos = p.xpath("./div/div/div[2]/descendant::p[@class='cssVocExEnglish']")
                sceneSentEns = [i.xpath('string(.)').strip() for i in sentInfos]
                sentInfos = p.xpath("./div/div/div[2]/descendant::p[@class='cssVocExChinese']")
                sceneSentChs = [i.xpath('string(.)').strip() for i in sentInfos]

                # 获取托福考试例句
                sentInfos = p.xpath("./div/div/div[3]/descendant::p[@class='cssVocExEnglish']")
                toeflSentEns = [i.xpath('string(.)').strip() for i in sentInfos]
                sentInfos = p.xpath("./div/div/div[3]/descendant::p[@class='cssVocExChinese']")
                toeflSentChs = [i.xpath('string(.)').strip() for i in sentInfos]

                # 添加例句
                sentences = []
                if len(jianmingSentEns) == len(jianmingSentChs):
                    sentences += [{"english": e, "chinese": c, "source": self.source + "-jianming", "audioUrlUS": "",
                                   "audioUrlUK": ""}
                                  for e, c in zip(jianmingSentEns, jianmingSentChs)]
                if len(sceneSentEns) == len(sceneSentChs):
                    sentences += [{"english": e, "chinese": c, "source": self.source + "-scene", "audioUrlUS": "",
                                   "audioUrlUK": ""}
                                  for e, c in zip(sceneSentEns, sceneSentChs)]
                if len(toeflSentEns) == len(toeflSentChs):
                    sentences += [{"english": e, "chinese": c, "source": self.source + "-" + name, "audioUrlUS": "",
                                   "audioUrlUK": ""}
                                  for e, c in zip(toeflSentEns, toeflSentChs)]
                paraphrase = {"pos": pos, "english": "", "chinese": parapch, "Sentences": sentences,
                              "source": self.source}

                paraphrases.append(paraphrase)
            except Exception as e:
                print("Error: {}".format(repr(e)))
                pass
        return paraphrases

    def get_Inflections(self, html, lexicon, name="toefl"):
        """
        变形词提取.
        """
        out = {}
        try:
            words = html.xpath("//ul[@class='cssVocForMatVaried']/li/text()")
            names = html.xpath("//ul[@class='cssVocForMatVaried']/li/span/text()")
            assert len(words) == len(names)
            for w, n in zip(words, names):
                out[n] = w.strip()
        except Exception:
            pass
        return out

    def get_Collocations(self, html, lexicon, name="toefl"):
        """
        搭配提取.
        """
        outs = []
        try:
            result = html.xpath("//ul[@class='cssVocTiemPanelContant jsVocTiemPanelContant']/li[2]/div/ul/li/ul/li")
            outs = []
            for r in result:
                en = r.xpath("string(descendant::p[@class='cssVocTotoleChinese'])").strip()
                ch = r.xpath("string(descendant::p[@class='cssVocTotoleEng'])").strip()
                outs.append({"name": en, "chinese": ch, "source": self.source})
        except Exception:
            pass
        return outs

    def get_Derivatives(self, html, lexicon, name="toefl"):
        """
        派生词提取.
        """
        outs = []
        try:
            id = html.xpath("//body")[0].attrib["data-word_id"]
            html = etree.parse(
                f"http://top.zhan.com/vocab/detail/one-2-ten.html?test_type=2&word_id={id}&word={lexicon}",
                etree.HTMLParser(encoding="utf-8"))
            ens = html.xpath("//p[@class='cssDeriWordsBoxId']/text()")
            chs = html.xpath("//ul[@class='cssDeriWordsBoxType']/li/text()")
            assert len(ens) == len(chs)
            for en, ch in zip(ens, chs):
                para = ch.split(".", 1)
                if len(para) != 2:
                    continue
                pos = para[0].strip() + "."
                parapch = para[1].strip()
                outs.append({"name": en.strip(), "chinese": parapch, "pos": pos, "source": self.source})
        except Exception:
            pass
        return outs

    def get_WordFormations(self, html, lexicon, name="toefl"):
        """
        构词法提取.
        """
        outs = []
        try:
            ens = html.xpath("//div[@class='cssVocWordPaneler jsVocWordPaneler']/span/text()")
            chs = html.xpath("//div[@class='cssVocWordDet jsVocWordDet']/div/span/text()")
            assert len(ens) == len(chs)
            expl = html.xpath("string(//p[@class='cssVocWordInter colorBlue']/text())").strip()
            out = {"formations": [], "paraphrase": expl, "source": self.source}
            for e, c in zip(ens, chs):
                value = {"english": e, "chinese": c}
                if e != "" and c != "":
                    out["formations"].append(value)
            if out["formations"]:
                name = " + ".join([i["english"] + "(" + i["chinese"] + ")" for i in out["formations"]]) + " = " + expl
                out["name"] = name
                outs = [out]
        except Exception:
            outs = []
        return outs

    def get_RootAffixs(self, html, lexicon, name="toefl"):
        """
        词根词缀提取.
        """
        outs = []
        try:
            id = html.xpath("//body")[0].attrib["data-word_id"]
            html = etree.parse(
                f"http://top.zhan.com/vocab/detail/one-2-ten.html?test_type=2&word_id={id}&word={lexicon}",
                etree.HTMLParser(encoding="utf-8"))
            contents = html.xpath("//div[@class='cssVocRootAffixBox']/div[@class='cssVocForMatTitle']/text()")
            has_root = False
            for content in contents:
                content = content.strip().split("=")
                if len(content) == 2:
                    e, c = content[0].strip(), content[1].strip()
                    if lexicon.startswith(e):
                        if e in Prefixs:
                            value = Prefixs[e]
                        elif e in Roots:
                            value = Roots[e]
                            has_root = True
                        else:
                            if has_root:
                                value = {"name": e, "type": "Prefix", "paraphrase": "", "origin": ""}
                            else:
                                value = {"name": e, "type": "Root", "paraphrase": "", "origin": ""}
                                has_root = True
                    elif lexicon.endswith(e):
                        if e in Suffixs:
                            value = Suffixs[e]
                        elif e in Roots:
                            value = Roots[e]
                            has_root = True
                        else:
                            if has_root:
                                value = {"name": e, "type": "Suffix", "paraphrase": "", "origin": ""}
                            else:
                                value = {"name": e, "type": "Root", "paraphrase": "", "origin": ""}
                                has_root = True
                    else:
                        if has_root:
                            if e in Prefixs:
                                value = Prefixs[e]
                            elif e in Suffixs:
                                value = Suffixs[e]
                            elif e in Roots:
                                value = Roots[e]
                                has_root = True
                            else:
                                value = {"name": e, "type": "Suffix", "paraphrase": "", "origin": ""}
                        else:
                            if e in Prefixs:
                                value = Prefixs[e]
                            elif e in Roots:
                                value = Roots[e]
                                has_root = True
                            elif e in Suffixs:
                                value = Suffixs[e]
                            else:
                                value = {"name": e, "type": "Root", "paraphrase": "", "origin": ""}
                    value["source"] = self.source
                    outs.append(value)
        except Exception:
            pass
        return outs

    def get_SynonymAntonyms(self, html, lexicon, name="toefl"):
        """
        同反义词提取.
        """
        outs = []
        try:
            contents = html.xpath("//div[@class='cssVocContAntonyms']")
            for content in contents:
                tag = content.xpath("string(./p)").strip()
                pp = content.xpath("string(./div[@class='cssVocAntonyMsChinese'])").strip().split(".", 1)
                words = content.xpath("./div[@class='cssVocAntonyMsEng']/a/span/text()")
                if len(pp) == 2:
                    pos = pp[0].strip() + "."
                    pp = pp[1].strip()
                    if tag == "同义词":
                        value = {"type": "Synonym", "paraphrase": pp, "lexicon": lexicon, "pos": pos, "words": words,
                                 "source": self.source}
                        outs.append(value)
                    elif tag == "反义词":
                        value = {"type": "Antonym", "paraphrase": pp, "lexicon": lexicon, "pos": pos, "words": words,
                                 "source": self.source}
                        outs.append(value)
        except Exception:
            pass
        return outs

    def save_infos(self, lexicon, infos):
        """
        保存词汇信息.
        """
        with open(self.dictPath + str(lexicon), "w", encoding="utf-8") as f:
            json.dump(infos, f, ensure_ascii=False)

    def read_infos(self, lexicon):
        """
        读取词汇信息.
        """
        with open(self.dictPath + str(lexicon), "r", encoding="utf-8") as f:
            return json.load(f)


if __name__ == "__main__":
    c = XiaozhanCrawler()
    c.get_infos("claim")


    def crawler():
        from multiprocessing import Pool
        with open("../../nlp_central_vocabulary/src/writer/en_tf-v1.0.json", "r", encoding="utf-8") as f:
            tf_dicts = {i['word'].strip(): i['frequency'] for i in json.load(f) if i['word'].strip()}
        words = list(tf_dicts.keys())
        print("{} words:".format(len(words)))
        p = Pool(8)
        for i in range(len(words)):
            if i % 100 == 0:
                print(i)
            p.apply_async(c.get_infos, (words[i].strip(),))
        p.close()
        p.join()


    crawler()
