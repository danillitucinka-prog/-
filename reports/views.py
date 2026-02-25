from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from . import bp
from models import db, Post, Report
from forms import ReportForm


@bp.route('/post/<int:post_id>/report', methods=['GET', 'POST'])
@login_required

def report_post(post_id):
    post = Post.query.get_or_404(post_id)
    form = ReportForm()

    if form.validate_on_submit():
        report = Report(
            reporter_id=current_user.id,
            post_id=post.id,
            reason=form.reason.data,
            description=form.description.data
        )
        db.session.add(report)
        db.session.commit()
        flash('Отчет отправлен модераторам', 'success')
        return redirect(url_for('posts.view_post', post_id=post.id))

    return render_template('report.html', form=form, post=post)