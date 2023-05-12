### Request and response headers
HTTP headers allow a client and server to pass additional information with a request or response. By rewriting these headers, you can accomplish important tasks, such as adding security-related header fields like HSTS/ X-XSS-Protection, removing response header fields that might reveal sensitive information, and removing port information from X-Forwarded-For headers.

Application Gateway allows you to add, remove, or update HTTP request and response headers while the request and response packets move between the client and back-end pools.

### Rewrite actions
You use rewrite actions to specify the URL, request headers or response headers that you want to rewrite and the new value to which you intend to rewrite them to. The value of a URL or a new or existing header can be set to these types of values:
- Text
- Request header. To specify a request header, you need to use the syntax ***{http_req_headerName}***
- Respons header. To specify a response header, you need to use the syntax ***{http_resp_headerName}***
- Server variable. To specify a server variable, you need to use the syntax ***{var_serverVariable}***. See the list of supported server variables.
- A combination of text, a request header, a response header, and a server variable.

***Example: Convert Nginx Rules to Application Gateway***

***nginx.conf***
```nginx
proxy_set_header HOST $host;    
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
```

The first step is to identify the server variable in Azure. See the mapping table below.
e.g. `$remote_addr` => `client_ip`
Then, set the header in Azure using the correct syntax, `{var_client_ip}`

***Application Gateway Rewrite Rules in Bicep***

```bicep
rewriteRuleSets = [
  {
    name = "SSL-Offloaded"
    properties = {
      rewriteRules = [
        {
          ruleSequence: 100,
          conditions: [],
          name: "RewriteHeaders",
          actionSet = {
            requestHeaderConfigurations: [
              {
                headerName: "HOST",
                headerValue: "{var_host}"
              },
              {
                headerName: "X-Forwarded-For",
                headerValue: "{var_add_x_forwarded_for_proxy}"
              }
            ],
            "responseHeaderConfigurations": []
          }
        },
        {
          ruleSequence: 101,
          conditions: [],
          name: "CustomHeader",
          actionSet: {
            requestHeaderConfigurations: [],
            responseHeaderConfigurations: [
              {
                headerName: "X-Real-IP",
                headerValue: "{var_client_ip}"
              },
              {
                headerName: "ClientPort",
                headerValue: "{var_client_port}"
              }
            ]
          }
        }
      ]
    }
  }
]
        
```
| Nginx Header | Azure Server Variable | Definition  |  
|---|---|---|
| $proxy_add_x_forwarded_for | add_x_forwarded_for_proxy | The X-Forwarded-For client request header field with the client_ip variable (see explanation later in this table) appended to it in the format IP1, IP2, IP3, and so on. If the X-Forwarded-For field isn't in the client request header, the add_x_forwarded_for_proxy variable is equal to the $client_ip variable. This variable is particularly useful when you want to rewrite the X-Forwarded-For header set by Application Gateway so that the header contains only the IP address without the port information. |
| $ssl_ciphers | ciphers_supported | A list of the ciphers supported by the client. |
| $ssl_cipher | ciphers_used | The IP address of the client from which the application gateway received the request. If there's a reverse proxy before the application gateway and the originating client, client_ip will return the IP address of the reverse proxy. |
| $remote_addr | client_ip| The client port. |
| $remote_port | client_port | The client port. |
| $tcpinfo_rtt | client_tcp_rtt | Information about the client TCP connection. Available on systems that support the TCP_INFO socket option. | 
| $remote_user |client_user | When HTTP authentication is used, the user name supplied for authentication. |
| \$host / \$hostname | host | In this order of precedence: the host name from the request line, the host name from the Host request header field, or the server name matching a request. Example: In the request http://contoso.com:8080/article.aspx?id=123&title=fabrikam, host value will be is contoso.com |
| $cookie_name | cookie_name | The name of a cookie |
| $request_method | http_method | The method used to make the URL request. For example, GET or POST. |
| $status | http_status | The session status. For example, 200, 400, or 403. |
| $server_protocol | http_version | The request protocol. Usually HTTP/1.0, HTTP/1.1, or HTTP/2.0. |
| $query_string | query_string | The list of variable/value pairs that follows the "?" in the requested URL. Example: In the request http://contoso.com:8080/article.aspx?id=123&title=fabrikam, query_string value will be id=123&title=fabrikam |
| $request_length | received_bytes | The length of the request (including the request line, header, and request body).|
| $request | request_query | The arguments in the request line. |
| $scheme | request_scheme | The request scheme: http or https. |
| $request_uri | request_uri | The full original request URI (with arguments). Example: in the request http://contoso.com:8080/article.aspx?id=123&title=fabrikam*, request_uri value will be /article.aspx?id=123&title=fabrikam | 
| $bytes_sent | sent_bytes | The number of bytes sent to a client. |
| $server_port | server_port | The port of the server that accepted a request. |
| $ssl_protocol | ssl_connection_protocol | The protocol of an established TLS connection. |
| $https | ssl_enabled | "On" if the connection operates in TLS mode. Otherwise, an empty string.|
| $uri | uri_path | Identifies the specific resource in the host that the web client wants to access. This is the part of the request URI without the arguments. Example: In the request http://contoso.com:8080/article.aspx?id=123&title=fabrikam, uri_path value will be /article.aspx |
| $ssl_client_escaped_cert | client_certificate | The client certificate in PEM format for an established SSL connection. |
| $ssl_client_v_end | client_certificate_end_date | The end date of the client certificate. |
| $ssl_client_fingerprint | client_certificate_fingerprint | The SHA1 fingerprint of the client certificate for an established SSL connection. |
| $ssl_client_i_dn |client_certificate_issuer| The "issuer DN" string of the client certificate for an established SSL connection. |
| $ssl_client_serial | client_certificate_serial | The serial number of the client certificate for an established SSL connection. |
| $ssl_client_v_start | client_certificate_start_date | The start date of the client certificate. |
| $ssl_client_s_dn_legacy | client_certificate_subject | The "subject DN" string of the client certificate for an established SSL connection. |
| $ssl_client_verify | client_certificate_verification | The result of the client certificate verification: SUCCESS, FAILED:\<reason\>, or NONE if a certificate was not present. |
