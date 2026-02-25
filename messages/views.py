from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from . import bp
from models import db, Message, User, Notification
from forms import SendMessageForm


@bp.route('/messages')
@login_required

def inbox():
    page = request.args.get('page', 1, type=int)
    messages = Message.query.filter_by(recipient_id=current_user.id).order_by(
        Message.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('messages/inbox.html', messages=messages)


@bp.route('/messages/<int:message_id>')
@login_required

def view_message(message_id):
    message = Message.query.get_or_404(message_id)

    if message.recipient_id != current_user.id:
        flash('Вы не можете просматривать это сообщение', 'danger')
        return redirect(url_for('messages.inbox'))

    message.is_read = True
    db.session.commit()
    return render_template('messages/view.html', message=message)


@bp.route('/messages/send/<username>', methods=['GET', 'POST'])
@login_required

def send_message(username):
    recipient = User.query.filter_by(username=username).first_or_404()

    if recipient == current_user:
        flash('Вы не можете написать себе', 'danger')
        return redirect(url_for('users.user_profile', username=username))

    form = SendMessageForm()
    form.recipient.data = recipient.username
    form.recipient.render_kw = {'readonly': True}

    if form.validate_on_submit():
        message = Message(
            sender_id=current_user.id,
            recipient_id=recipient.id,
            subject=form.subject.data,
            content=form.content.data
        )
        current_user.add_log('send_message', f'Sent message to {recipient.username}')
        db.session.add(message)
        db.session.commit()

        notification = Notification(
            user_id=recipient.id,
            notification_type='message',
            title=f'Новое сообщение от {current_user.username}',
            content=form.subject.data,
            link=url_for('messages.view_message', message_id=message.id)
        )
        db.session.add(notification)
        db.session.commit()

        flash('Сообщение отправлено', 'success')
        return redirect(url_for('messages.inbox'))

    return render_template('messages/send.html', form=form, recipient=recipient)