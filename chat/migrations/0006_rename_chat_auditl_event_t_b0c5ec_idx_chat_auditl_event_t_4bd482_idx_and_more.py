from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("chat", "0005_backfill_runtime_tables_on_default"),
    ]

    operations = [
        migrations.RenameIndex(
            model_name="auditlog",
            new_name="chat_auditl_event_t_4bd482_idx",
            old_name="chat_auditl_event_t_b0c5ec_idx",
        ),
        migrations.RenameIndex(
            model_name="auditlog",
            new_name="chat_auditl_outcome_d25cda_idx",
            old_name="chat_auditl_outcome_88e790_idx",
        ),
        migrations.RenameIndex(
            model_name="auditlog",
            new_name="chat_auditl_created_caef1a_idx",
            old_name="chat_auditl_created_7d2ac9_idx",
        ),
        migrations.RenameIndex(
            model_name="chatmessage",
            new_name="chat_chatme_chat_se_3964f8_idx",
            old_name="chat_chatme_chat_se_b22aa9_idx",
        ),
        migrations.RenameIndex(
            model_name="chatmessage",
            new_name="chat_chatme_role_5fee23_idx",
            old_name="chat_chatme_role_12532e_idx",
        ),
        migrations.RenameIndex(
            model_name="chatsession",
            new_name="chat_chatse_vector__9b5a50_idx",
            old_name="chat_chats_vector__5d5d73_idx",
        ),
        migrations.RenameIndex(
            model_name="chatsession",
            new_name="chat_chatse_session_ff16c0_idx",
            old_name="chat_chats_session_63bb74_idx",
        ),
        migrations.RenameIndex(
            model_name="crawljob",
            new_name="chat_crawlj_status_ab978d_idx",
            old_name="chat_crawlj_status_6d2677_idx",
        ),
        migrations.RenameIndex(
            model_name="crawljob",
            new_name="chat_crawlj_vector__8fdcc2_idx",
            old_name="chat_crawlj_vector__f1a2c5_idx",
        ),
        migrations.RenameIndex(
            model_name="messagefeedback",
            new_name="chat_messag_rating_4652d5_idx",
            old_name="chat_messag_rating_47f8ec_idx",
        ),
    ]
