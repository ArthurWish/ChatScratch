from flask import Flask, Response, jsonify, redirect, request, send_file, send_from_directory, render_template

app = Flask(__name__)



if __name__ == '__main__':
    app.run()