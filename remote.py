import subprocess
import xml.etree.ElementTree as ET

from svn.exceptions import SvnException
from utils import render_logger


def xml_to_dict(xml_text: str):
    xml_tree = ET.fromstring(xml_text)
    results = xml_tree.findall('./version')
    if not results:
        return None
    return results[0].text


class RemoteSubversion:
    show_execute_query = True

    def __init__(self, username: str, password: str, url_repository: str):
        """

        :param username: username for auth in svn
        :param password: password for auth in svn
        :param url_repository: url repository
        """
        self.__username = username
        self.__password = password
        self.__url_repository = url_repository
        self.__logger__ = render_logger('RemoteSubversion')

    @property
    def logger(self):
        return self.__logger__

    def get_url(self, url):
        return '%s%s' % (self.__url_repository, url)

    @staticmethod
    def _render_kwargs(**kwargs):
        result = []
        for key in kwargs.keys():
            if kwargs[key] is not None:
                result.append("--%s %s" % (key, kwargs[key]))
            else:
                result.append("--%s" % key)

        return " ".join(result)

    def _render_auth(self, safe: bool=False):
        if safe:
            return self._render_kwargs(username='*' * 7, password='*' * 7)
        return self._render_kwargs(username=self.__username, password=self.__password, )

    def _safe_string(self, string: str):
        return string.replace(self._render_auth(), self._render_auth(safe=True))

    def _execute(self, query: str):
        """
        Execute query in console and return result

        :param query: query

        :return:
        """

        if self.show_execute_query:
            self.logger.debug(self._safe_string(query))

        p = subprocess.Popen(
            query,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True)

        output = p.stdout.read()
        r = p.wait()
        p.stdout.close()

        if r != 0:
            raise SvnException(
                self._safe_string(
                    "Command failed with ({}): {}\n{}".format(
                        p.returncode, query, output)))

        return output if output is None else output.decode('utf-8')

    def simple_query(self, command: str, url: str, use_xml_format: bool=False, *args, **kwargs):
        """

        :param command:
        :param url:
        :param use_xml_format: query
        :param args:
        :param kwargs:
        :return:
        """
        url = '%s%s' % (self.__url_repository, url)
        query_list = [
            'svn', command, self._render_auth(), self._render_kwargs(**kwargs),
            '' if not use_xml_format else '--xml',
            url]
        query = ' '.join([x for x in query_list if x])
        return self._execute(query)

    def copy(self, url_donor: str, url_recipient: str, use_xml_format: bool=False, *args, **kwargs):

        query_list = [
            'svn', 'copy', self._render_auth(), self._render_kwargs(**{'non-interactive': None}),
            '' if not use_xml_format else '--xml',
            ' -m "Create new test tag for %s."' % url_donor,
            self.get_url(url_donor), self.get_url(url_recipient)]
        query = ' '.join([x for x in query_list if x])
        return self._execute(query)

    def info(self, url: str):
        return self.simple_query(command='info', url=url)

    def log(self, url: str):
        return self.simple_query(command='log', url=url)

    def list(self, url: str):
        return self.simple_query(command='list', url=url)

    def revision(self, url: str, start_revision: str, end_revision: str):
        return self.simple_query(
            command='log', url=url, revision="%s:%s" % (start_revision.strip(), end_revision.strip()))

    @staticmethod
    def xml_to_dict(xml_text):
        xml_to_dict(xml_text)


#  --no-auth-cache
# -- non-interactive
