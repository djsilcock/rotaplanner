
from flask import request,Response,Flask,g
from unpoly.adapter import BaseAdapter
from typing import Mapping,cast
from unpoly import Unpoly

class FlaskAdapter(BaseAdapter):
    
    def request_headers(self) -> Mapping[str, str]:
        return request.headers

    def request_params(self) -> Mapping[str, str]:
        return request.args

    def redirect_uri(self, response: Response) -> str | None:  # noqa: ARG002
        return response.location

    def set_redirect_uri(self, response: Response, uri: str) -> None:  # noqa: ARG002
        response.location=uri

    def set_headers(
        self, response: Response, headers: Mapping[str, str]  # noqa: ARG002
    ) -> None:
        for  name,value in headers.items():
            response.headers.add(name,value)

    def set_cookie(
        self, response: Response, needs_cookie: bool = False  # noqa: ARG002
    ) -> None:
        self.cookie = needs_cookie
        if needs_cookie:
            response.set_cookie('_up_method',self.method)
        else:
            response.delete_cookie('_up_cookie')

    @property
    def method(self) -> str:
        return request.method

    @property
    def location(self) -> str:
        return request.url

class FlaskUnpoly:
    def init_app(self,app:Flask):
        @app.before_request
        def before_request():
            g.unpoly=Unpoly(FlaskAdapter())
        @app.after_request
        def after_request(response):
            cast(Unpoly,g.unpoly).finalize_response(response)
            return response
        app.add_template_global(unpoly)

def unpoly()->Unpoly:
    return g.unpoly